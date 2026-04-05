from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.domain import Event, URL, User
from app.models.schemas import EventCreate, EventOut
from app.cache import get_redis_client, get_cache, invalidate_cache, set_cache


router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventOut, status_code=status.HTTP_201_CREATED)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    if not db.query(User).filter(User.id == event.user_id).first():
        raise HTTPException(status_code=404, detail="User not found")
    if not db.query(URL).filter(URL.id == event.url_id).first():
        raise HTTPException(status_code=404, detail="URL not found")

    db_event = Event(
        url_id=event.url_id,
        user_id=event.user_id,
        event_type=event.event_type,
        details=event.details,
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    invalidate_cache(get_redis_client(), "events:*")
    return db_event


@router.get("", response_model=List[EventOut])
def get_events(
    skip: int = 0,
    limit: int = 100,
    url_id: Optional[int] = None,
    user_id: Optional[int] = None,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    redis_client = get_redis_client()
    # Cache key includes all filter parameters
    cache_key = f"events:skip={skip}:limit={limit}:url_id={url_id}:user_id={user_id}:type={event_type}"
    
    cached = get_cache(redis_client, cache_key)
    if cached is not None:
        return cached

    query = db.query(Event)
    if url_id is not None:
        query = query.filter(Event.url_id == url_id)
    if user_id is not None:
        query = query.filter(Event.user_id == user_id)
    if event_type is not None:
        query = query.filter(Event.event_type == event_type)
    
    events = query.order_by(Event.id).offset(skip).limit(limit).all()
    events_out = [EventOut.model_validate(e) for e in events]
    
    set_cache(redis_client, cache_key, events_out, ttl=15)
    return events_out
