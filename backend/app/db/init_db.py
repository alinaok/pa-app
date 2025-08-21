# Import all models so SQLAlchemy knows about them
from app.models import user, mood, task, reminder, symptom
from app.models.base import Base
from app.db.session import engine


# Create the tables in your database using your models.
Base.metadata.create_all(bind=engine)