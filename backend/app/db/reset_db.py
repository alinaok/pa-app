# Import all models so Base.metadata knows about them
from app.models import user, mood, task, reminder, symptom
from app.models.base import Base
from app.db.session import engine

if __name__ == "__main__":
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Done.")