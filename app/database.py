from sqlalchemy import create_engine, Column, Integer, String, DateTime, insert
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import os

Base = declarative_base()
DB_PATH = os.path.join(os.getenv("DATA_DIR", "./data"), "queue.db")
engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)

class DownloadQueue(Base):
    __tablename__ = "download_queue"
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    Base.metadata.create_all(engine)

def add_to_queue(url: str):
    with Session() as session:
        stmt = insert(DownloadQueue).values(url=url).prefix_with("OR IGNORE", dialect="sqlite")
        session.execute(stmt)
        session.commit()

def get_pending():
    with Session() as session:
        return session.query(DownloadQueue).filter_by(status="pending").all()