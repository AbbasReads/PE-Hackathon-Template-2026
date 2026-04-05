import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from app.database import Base, engine, SessionLocal
from app.routes import users, urls, events
from app.models.domain import User, URL, Event
import csv
import json

app = FastAPI(title="Hackathon URL Shortener", default_response_class=ORJSONResponse)

Base.metadata.create_all(bind=engine)

app.include_router(users.router)
app.include_router(urls.router)
app.include_router(events.router)


def seed_database():
    db = SessionLocal()
    if not db.query(User).first():
        print("Seeding database...")
        try:
            with open("seed_data/users.csv", "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    db.add(User(id=int(row['id']), username=row['username'], email=row['email']))
            db.commit()
            
            with open("seed_data/urls.csv", "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    is_active = row['is_active'].lower() == 'true'
                    db.add(URL(id=int(row['id']), user_id=int(row['user_id']), short_code=row['short_code'], original_url=row['original_url'], title=row['title'], is_active=is_active))
            db.commit()
            
            with open("seed_data/events.csv", "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    details = json.loads(row['details'].replace("'", '"')) if row['details'] else {}
                    db.add(Event(id=int(row['id']), url_id=int(row['url_id']), user_id=int(row['user_id']), event_type=row['event_type'], details=details))
            db.commit()
            
            # Reset auto-increment sequences for PostgreSQL
            from sqlalchemy import text
            db.execute(text("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))"))
            db.execute(text("SELECT setval('urls_id_seq', (SELECT MAX(id) FROM urls))"))
            db.execute(text("SELECT setval('events_id_seq', (SELECT MAX(id) FROM events))"))
            db.commit()
            
            print("Database seeded successfully.")
        except Exception as e:
            print(f"Error seeding database: {e}")
            db.rollback()
    db.close()

seed_database()

if __name__ == "__main__":
    uvicorn.run("run:app", host="0.0.0.0", port=8000, workers=4)
