import csv
import io
import random
import string
from sqlalchemy.orm import Session
from app.models.domain import URL
from typing import List, Dict

def parse_users_csv(file_content: str) -> List[Dict[str, str]]:
    users = []
    try:
        reader = csv.DictReader(io.StringIO(file_content))
        if not reader.fieldnames:
            raise ValueError("CSV must include headers")

        normalized_headers = {field.strip().lower() for field in reader.fieldnames if field}
        if "username" not in normalized_headers or "email" not in normalized_headers:
            raise ValueError("CSV must include username and email columns")

        seen_emails = set()
        for row in reader:
            if None in row:
                raise ValueError("Malformed CSV data")

            username = (row.get("username") or "").strip()
            email = (row.get("email") or "").strip().lower()
            if username and email and email not in seen_emails:
                users.append({"username": username, "email": email})
                seen_emails.add(email)
    except csv.Error as exc:
        raise ValueError("Malformed CSV data") from exc
    return users

def generate_short_code(db: Session, length: int = 6) -> str:
    characters = string.ascii_letters + string.digits
    while True:
        short_code = ''.join(random.choices(characters, k=length))
        if not db.query(URL).filter(URL.short_code == short_code).first():
            return short_code
