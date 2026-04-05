from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.database import get_db, SessionLocal
from app.models.domain import Event, URL, User
from app.models.schemas import URLCreate, URLOut, URLUpdate
from app.utils import generate_short_code
from app.cache import get_redis_client, get_cache, set_cache, invalidate_cache


router = APIRouter(prefix="/urls", tags=["urls"])


def _log_event(
    url_id: int,
    user_id: int,
    event_type: str,
    details: dict,
    session_factory: sessionmaker,
) -> None:
    """Background task: logs an event without blocking the response."""
    db = session_factory()
    try:
        db.add(Event(url_id=url_id, user_id=user_id, event_type=event_type, details=details))
        db.commit()
        invalidate_cache(get_redis_client(), "events:*")
    finally:
        db.close()



def _schedule_event(
    background_tasks: BackgroundTasks,
    db: Session,
    *,
    url_id: int,
    user_id: int,
    event_type: str,
    details: dict,
) -> None:
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=db.get_bind())
    background_tasks.add_task(
        _log_event,
        url_id=url_id,
        user_id=user_id,
        event_type=event_type,
        details=details,
        session_factory=session_factory,
    )


def _create_url_record(db: Session, url: URLCreate) -> tuple[URL, str]:
    for _ in range(20):
        short_code = generate_short_code(db)
        db_url = URL(
            user_id=url.user_id,
            original_url=str(url.original_url),
            title=url.title,
            short_code=short_code,
        )
        db.add(db_url)
        try:
            db.commit()
            db.refresh(db_url)
            return db_url, short_code
        except IntegrityError:
            db.rollback()

    raise HTTPException(status_code=503, detail="Unable to generate a unique short code")


@router.post("", response_model=URLOut, status_code=status.HTTP_201_CREATED)
def create_url(url: URLCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == url.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_url, short_code = _create_url_record(db, url)
    
    invalidate_cache(get_redis_client(), "urls:*")
    _schedule_event(
        background_tasks,
        db,
        url_id=db_url.id,
        user_id=url.user_id,
        event_type="created",
        details={"short_code": short_code, "original_url": str(url.original_url)},
    )
    return db_url


@router.get("", response_model=List[URLOut])
def get_urls(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    redis_client = get_redis_client()
    cache_key = f"urls:user_id={user_id}:is_active={is_active}:skip={skip}:limit={limit}"
    cached = get_cache(redis_client, cache_key)
    if cached is not None:
        return cached

    query = db.query(URL)
    if user_id is not None:
        query = query.filter(URL.user_id == user_id)
    if is_active is not None:
        query = query.filter(URL.is_active == is_active)
    urls = query.order_by(URL.id).offset(skip).limit(limit).all()
    urls_out = [URLOut.model_validate(u) for u in urls]
    set_cache(redis_client, cache_key, urls_out, ttl=30)
    return urls_out


@router.get("/{id}", response_model=URLOut)
def get_url(id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    redis_client = get_redis_client()
    cache_key = f"url:{id}"
    cached = get_cache(redis_client, cache_key)
    if cached is not None:
        _schedule_event(
            background_tasks, db, url_id=id, user_id=cached["user_id"],
            event_type="accessed", details={"short_code": cached["short_code"], "original_url": cached["original_url"]}
        )
        return cached

    url = db.query(URL).filter(URL.id == id).first()
    if not url or not url.is_active:
        raise HTTPException(status_code=404, detail="URL not found")

    url_out = URLOut.model_validate(url)
    set_cache(redis_client, cache_key, url_out, ttl=60)
    
    _schedule_event(
        background_tasks,
        db,
        url_id=url.id,
        user_id=url.user_id,
        event_type="accessed",
        details={"short_code": url.short_code, "original_url": url.original_url},
    )
    return url


@router.get("/{short_code}/redirect")
def redirect_short_code(short_code: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    url = db.query(URL).filter(URL.short_code == short_code).first()
    if not url or not url.is_active:
        raise HTTPException(status_code=404, detail="URL not found")

    _schedule_event(
        background_tasks,
        db,
        url_id=url.id,
        user_id=url.user_id,
        event_type="click",
        details={"short_code": url.short_code, "original_url": url.original_url},
    )
    return RedirectResponse(url=url.original_url, status_code=status.HTTP_302_FOUND)


@router.put("/{id}", response_model=URLOut)
def update_url(id: int, url_update: URLUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_url = db.query(URL).filter(URL.id == id).first()
    if not db_url:
        raise HTTPException(status_code=404, detail="URL not found")

    if url_update.title is not None:
        db_url.title = url_update.title
    if url_update.is_active is not None:
        db_url.is_active = url_update.is_active

    db.commit()
    db.refresh(db_url)
    
    redis_client = get_redis_client()
    invalidate_cache(redis_client, f"url:{id}")
    invalidate_cache(redis_client, "urls:*")

    _schedule_event(
        background_tasks,
        db,
        url_id=db_url.id,
        user_id=db_url.user_id,
        event_type="updated",
        details={"short_code": db_url.short_code, "original_url": str(db_url.original_url)},
    )
    return db_url


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_url(id: int, db: Session = Depends(get_db)) -> Response:
    db_url = db.query(URL).filter(URL.id == id).first()
    if not db_url:
        raise HTTPException(status_code=404, detail="URL not found")

    db.query(Event).filter(Event.url_id == id).delete(synchronize_session=False)
    db.delete(db_url)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
