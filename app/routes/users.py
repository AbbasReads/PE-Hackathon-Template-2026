from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.domain import User
from app.models.schemas import UserCreate, UserOut, UserUpdate
from typing import List
from app.utils import parse_users_csv
from pydantic import ValidationError

router = APIRouter(prefix="/users", tags=["users"])


def _get_existing_user_keys(db: Session) -> tuple[set[str], set[str]]:
    existing_emails = {email for (email,) in db.query(func.lower(User.email)).all()}
    existing_usernames = {username for (username,) in db.query(func.lower(User.username)).all()}
    return existing_emails, existing_usernames

@router.post("/bulk", response_model=dict)
async def create_users_bulk(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files allowed")
    
    content = await file.read()
    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded") from exc

    try:
        parsed_users = parse_users_csv(text_content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    
    count = 0
    existing_emails, existing_usernames = _get_existing_user_keys(db)
    for user_data in parsed_users:
        try:
            # Simple validation using pure pydantic
            schema = UserCreate(username=user_data["username"], email=user_data["email"])
            normalized_email = schema.email.lower()
            normalized_username = schema.username.lower()
            if normalized_email not in existing_emails and normalized_username not in existing_usernames:
                db_user = User(username=schema.username, email=normalized_email)
                db.add(db_user)
                count += 1
                existing_emails.add(normalized_email)
                existing_usernames.add(normalized_username)
        except ValidationError:
            pass  # Skip invalid rows
    
    db.commit()
    return {"count": count}

@router.get("", response_model=List[UserOut])
def get_users(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * per_page
    users = db.query(User).offset(skip).limit(per_page).all()
    return users

@router.get("/{id}", response_model=UserOut)
def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    normalized_email = user.email.lower()
    normalized_username = user.username.lower()
    if db.query(User).filter(func.lower(User.email) == normalized_email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(func.lower(User.username) == normalized_username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    db_user = User(username=user.username, email=normalized_email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.put("/{id}", response_model=UserOut)
def update_user(id: int, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.username is not None:
        normalized_username = user.username.lower()
        existing_user = db.query(User).filter(func.lower(User.username) == normalized_username, User.id != id).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        db_user.username = user.username
        
    db.commit()
    db.refresh(db_user)
    return db_user
