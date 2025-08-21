from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base


# DATABASE_URL = "postgresql://user:password@localhost/dbname"
DATABASE_URL = "postgresql://alina:postgres_pw@localhost:5432/assistant_app_db"

# Configure SQLAlchemy to connect to your PostgreSQL database.
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()