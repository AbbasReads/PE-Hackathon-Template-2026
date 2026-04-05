from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session, sessionmaker
from app.database import get_db
from app.models.domain import URL, User, Event
from app.models.schemas import URLCreate, URLOut, URLUpdate
from app.utils import generate_short_code
from typing import List, Optional


def _log_event(
    url_id: int,
    user_id: int,
    event_type: str,
    details: dict,
    session_factory: sessionmaker,
):
    """Background task: logs an event without blocking the response."""
    db = session_factory()
    try:
        db.add(Event(url_id=url_id, user_id=user_id, event_type=event_type, details=details))
        db.commit()
    finally:
        db.close()

router = APIRouter(prefix="/urls", tags=["urls"])

@router.post("", response_model=URLOut, status_code=status.HTTP_201_CREATED)
def create_url(url: URLCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == url.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    short_code = generate_short_code(db)
    
    db_url = URL(
        user_id=url.user_id,
        original_url=url.original_url,
        title=url.title,
        short_code=short_code
    )
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=db.get_bind())

    # Offload event logging to background — return response instantly
    background_tasks.add_task(
        _log_event, url_id=db_url.id, user_id=url.user_id,
        event_type="created",
        details={"short_code": short_code, "original_url": url.original_url},
        session_factory=session_factory,
    )
    
    return db_url

@router.get("", response_model=List[URLOut])
def get_urls(skip: int = 0, limit: int = 100, user_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(URL)
    if user_id is not None:
        query = query.filter(URL.user_id == user_id)
    return query.order_by(URL.id).offset(skip).limit(limit).all()

@router.get("/{id}", response_model=URLOut)
def get_url(id: int, db: Session = Depends(get_db)):
    url = db.query(URL).filter(URL.id == id).first()
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    return url

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
    
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=db.get_bind())

    # Offload event logging to background
    background_tasks.add_task(
        _log_event, url_id=db_url.id, user_id=db_url.user_id,
        event_type="updated",
        details={"short_code": db_url.short_code, "original_url": db_url.original_url},
        session_factory=session_factory,
    )
    
    return db_url
