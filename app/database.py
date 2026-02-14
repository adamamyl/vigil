from sqlalchemy import create_engine, Column, Integer, String, DateTime, insert
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import os

Base = declarative_base()

# Resolve the DB path dynamically
DATA_DIR = os.getenv("DATA_DIR", "./data")
DB_PATH = os.path.join(DATA_DIR, "queue.db")

# Setup the engine
engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)

class DownloadQueue(Base):
    __tablename__ = "download_queue"
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    status = Column(String, default="pending")  # pending, downloading, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    """
    Idempotent database initialization.
    Ensures the data directory exists before creating the SQLite file.
    """
    # Create the directory if it doesn't exist
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
        print(f"📁 Created missing data directory at: {DATA_DIR}")

    # Create tables if they don't exist
    Base.metadata.create_all(engine)

def add_to_queue(url: str):
    """Atomic insert using SQLite OR IGNORE logic."""
    with Session() as session:
        stmt = insert(DownloadQueue).values(url=url).prefix_with("OR IGNORE", dialect="sqlite")
        session.execute(stmt)
        session.commit()

def get_pending():
    """Fetches all items currently in the queue."""
    with Session() as session:
        return session.query(DownloadQueue).order_by(DownloadQueue.created_at.desc()).all()