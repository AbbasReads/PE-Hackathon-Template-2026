from typing import Annotated, Optional, Dict, Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, StrictBool, StrictStr
from datetime import datetime


StrictPositiveInt = Annotated[int, Field(strict=True, gt=0)]

class UserBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: StrictStr = Field(min_length=1, max_length=255)
    email: EmailStr

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: Optional[StrictStr] = Field(default=None, min_length=1, max_length=255)

class UserOut(UserBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class URLBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    original_url: HttpUrl
    title: StrictStr = Field(min_length=1, max_length=255)

class URLCreate(URLBase):
    user_id: StrictPositiveInt

class URLUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: Optional[StrictStr] = Field(default=None, min_length=1, max_length=255)
    is_active: Optional[StrictBool] = None

class URLOut(URLBase):
    id: int
    user_id: int
    short_code: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class EventBase(BaseModel):
    url_id: StrictPositiveInt
    user_id: StrictPositiveInt
    event_type: StrictStr = Field(min_length=1, max_length=100)
    details: Dict[str, Any]

class EventOut(EventBase):
    id: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)
