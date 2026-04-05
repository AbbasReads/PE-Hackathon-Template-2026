import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    database_host = os.environ.get("DATABASE_HOST")
    if database_host and database_host not in {"localhost", "127.0.0.1"}:
        DATABASE_URL = (
            f"postgresql://{os.environ.get('DATABASE_USER', 'postgres')}:"
            f"{os.environ.get('DATABASE_PASSWORD', 'postgres')}@"
            f"{database_host}:"
            f"{os.environ.get('DATABASE_PORT', '5432')}/"
            f"{os.environ.get('DATABASE_NAME', 'hackathon_db')}"
        )
    else:
        DATABASE_URL = "sqlite:///./app.db"

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs.update(
        pool_size=int(os.environ.get("DB_POOL_SIZE", "10")),
        max_overflow=int(os.environ.get("DB_MAX_OVERFLOW", "20")),
        pool_timeout=int(os.environ.get("DB_POOL_TIMEOUT", "30")),
        pool_pre_ping=True,
        pool_recycle=int(os.environ.get("DB_POOL_RECYCLE", "1800")),
        pool_use_lifo=True,
    )

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
