"""
Database configuration and initialization for Todo application.

Uses SQLite with SQLAlchemy ORM for persistent storage.
Includes indexes on frequently queried columns for optimal performance.
"""

import os
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    create_engine,
    Column,
    String,
    DateTime,
    ForeignKey,
    Index,
    event,
)
from sqlalchemy.types import Uuid
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship

# Database configuration
DB_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
DB_FILE = os.path.join(DB_DIR, "todos.db")
DATABASE_URL = f"sqlite:///{DB_FILE}"

# Create engine with SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite
    echo=False,  # Set to True for SQL query logging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


class TodoModel(Base):
    """
    SQLAlchemy model for Todo items.
    
    Indexes:
    - parent_uuid: For efficient queries by parent (hierarchical queries)
    - created_at: For sorting and time-based filtering
    - (parent_uuid, title): Composite index for searches within parent
    
    Relationships:
    - children: One-to-many relationship with other TodoModel instances
    """

    __tablename__ = "todos"

    uuid = Column(Uuid(as_uuid=True), primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(String(1024), nullable=True)
    parent_uuid = Column(Uuid(as_uuid=True), ForeignKey("todos.uuid"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship for accessing children
    children = relationship(
        "TodoModel",
        remote_side=[uuid],
        backref="parent",
        cascade="all, delete-orphan",
        foreign_keys=[parent_uuid],
        single_parent=True,
    )

    # Indexes for optimal query performance
    __table_args__ = (
        Index("idx_parent_uuid", "parent_uuid"),  # Query todos by parent
        Index("idx_created_at", "created_at"),  # Sort/filter by creation time
        Index("idx_parent_title", "parent_uuid", "title"),  # Search within parent
    )

    def __repr__(self):
        return f"TodoModel(uuid={self.uuid}, title={self.title}, parent_uuid={self.parent_uuid})"


# Enable foreign key support in SQLite (disabled by default)
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraint checking in SQLite."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)
    print(f"✓ Database initialized at: {DB_FILE}")


def get_db() -> Session:
    """Get a database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session() -> Session:
    """Get a new database session."""
    return SessionLocal()
