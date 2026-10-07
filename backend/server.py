import sqlite3
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

DB_FILE = "phone_records.db"

# Initialize SQLite database and create phone_records table if missing
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS phone_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rawTranscript TEXT NOT NULL,
            parsedNumber TEXT UNIQUE NOT NULL,
            language TEXT NOT NULL,
            collectedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Context manager or helper for DB connection
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# Pydantic schema for creating a phone record
class PhoneRecordCreate(BaseModel):
    rawTranscript: str
    parsedNumber: str
    language: str

# Pydantic schema for returning a phone record
class PhoneRecordResponse(BaseModel):
    id: int
    rawTranscript: str
    parsedNumber: str
    language: str
    collectedAt: str

from contextlib import asynccontextmanager

# Modern async context manager lifespan handler for DB setup
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

# Setup CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def ap():
    return {
        "health" : "working"
    }


# Save a new valid phone record into SQLite database
@app.post("/api/phone", response_model=PhoneRecordResponse, status_code=status.HTTP_201_CREATED)
def create_phone_record(record: PhoneRecordCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO phone_records (rawTranscript, parsedNumber, language) VALUES (?, ?, ?)",
            (record.rawTranscript, record.parsedNumber, record.language)
        )
        conn.commit()
        record_id = cursor.lastrowid
        cursor.execute("SELECT id, rawTranscript, parsedNumber, language, collectedAt FROM phone_records WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row)
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Phone number '{record.parsedNumber}' already exists in database."
        )
    except Exception as e:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Fetch all saved phone records ordered by collection timestamp descending
@app.get("/api/phone", response_model=List[PhoneRecordResponse])
def get_all_phone_records():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, rawTranscript, parsedNumber, language, collectedAt FROM phone_records ORDER BY collectedAt DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# Delete a stored phone record by its unique database ID
@app.delete("/api/phone/{record_id}", status_code=status.HTTP_200_OK)
def delete_phone_record(record_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM phone_records WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Phone record with ID {record_id} not found."
        )
    cursor.execute("DELETE FROM phone_records WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
    return {"message": f"Record with ID {record_id} successfully deleted."}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
