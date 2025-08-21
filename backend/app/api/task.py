from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
import app.crud.task
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut
from app.db.session import get_db
from app.models.task import Task, TaskStatus
from app.core.dependencies import get_current_user
from app.models.user import User
from datetime import datetime, timedelta
from sqlalchemy import or_, and_
from app.ai.task_helper import analyze_task_input
from app.services.google_calendar import GoogleCalendarService
import pytz


router = APIRouter(prefix="/tasks", tags=["tasks"])

# TaskOut is the Pydantic model used for output serialization.
@router.post("/", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Create a task and optionally schedule it in Google Calendar"""
    try:
        # Create task in database first
        created_task = app.crud.task.create_task(db, task, user_id=user.id)
        
        # Schedule in Google Calendar if due_date, preferred_time, or we want evening scheduling
        if task.due_date or task.preferred_time or (not task.due_date and not task.preferred_time):
            calendar_service = GoogleCalendarService()
            
            # Determine start time
            if task.preferred_time:
                # Use specified time
                start_time = datetime.combine(
                    task.due_date.date() if task.due_date else datetime.now().date(),
                    task.preferred_time
                )
                
                # Make timezone-aware
                local_tz = pytz.timezone('America/New_York')
                start_time = local_tz.localize(start_time)
                
                # Check if time is in the past for today
                now = datetime.now(local_tz)
                if not task.due_date and start_time < now:
                    # Schedule for tomorrow if no specific date and time is in the past
                    tomorrow = now + timedelta(days=1)
                    start_time = start_time.replace(
                        year=tomorrow.year,
                        month=tomorrow.month,
                        day=tomorrow.day
                    )
            elif task.due_date:
                # Find available slot on the due date
                available_slots = calendar_service.find_available_slots(task.due_date)
                
                if available_slots:
                    start_time = available_slots[0]  # First available slot
                else:
                    # Fallback to 11 AM
                    start_time = task.due_date.replace(hour=11, minute=0, second=0, microsecond=0)
                    local_tz = pytz.timezone('America/New_York')
                    start_time = local_tz.localize(start_time)
            else:
                # No due_date or preferred_time - find evening slot starting from today
                start_time = None
                current_date = datetime.now().date()
                
                # Try to find evening slot in the next 7 days
                for days_ahead in range(7):
                    target_date = current_date + timedelta(days=days_ahead)
                    
                    # Look for available slots after 6pm
                    evening_slots = calendar_service.find_available_slots(
                        target_date, 
                        start_hour=18,  # 6pm
                        end_hour=22     # 10pm
                    )
                    
                    if evening_slots:
                        start_time = evening_slots[0]
                        break
                
                # If no evening slots found, fallback to 6pm today or tomorrow
                if not start_time:
                    now = datetime.now()
                    if now.hour < 18:  # Before 6pm
                        start_time = now.replace(hour=18, minute=0, second=0, microsecond=0)
                    else:  # After 6pm, schedule for tomorrow
                        tomorrow = now + timedelta(days=1)
                        start_time = tomorrow.replace(hour=18, minute=0, second=0, microsecond=0)
                    
                    local_tz = pytz.timezone('America/New_York')
                    start_time = local_tz.localize(start_time)
            
            # Create recurrence rule if needed
            recurrence_rule = None
            if task.is_recurring and task.recurrence_pattern:
                if task.recurrence_pattern == "daily":
                    recurrence_rule = f"RRULE:FREQ=DAILY;INTERVAL={task.recurrence_interval or 1}"
                    if task.recurrence_end_date:
                        recurrence_rule += f";UNTIL={task.recurrence_end_date.strftime('%Y%m%d')}"
                elif task.recurrence_pattern == "weekly":
                    recurrence_rule = f"RRULE:FREQ=WEEKLY;INTERVAL={task.recurrence_interval or 1}"
                elif task.recurrence_pattern == "monthly":
                    recurrence_rule = f"RRULE:FREQ=MONTHLY;INTERVAL={task.recurrence_interval or 1}"
            
            # Create calendar event
            calendar_service.create_event(
                title=task.title,
                description=task.description or "",
                start_time=start_time,
                duration_minutes=60,  # Default duration, could be made configurable
                recurring=task.is_recurring,
                recurrence_rule=recurrence_rule
            )
        
        return created_task
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


def get_next_due_date(current_due_date, pattern, interval):
    if pattern == "daily":
        return current_due_date + timedelta(days=interval)
    elif pattern == "weekly":
        return current_due_date + timedelta(weeks=interval)
    elif pattern == "monthly":
        # For simplicity, add 30 days per month
        return current_due_date + timedelta(days=30 * interval)
    else:
        return None

@router.post("/{task_id}/complete", response_model=dict)
def complete_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = TaskStatus.completed
    task.completed_at = datetime.utcnow()  # Set completion timestamp
    db.commit()
    db.refresh(task)

    # Handle recurrence
    created_new = False
    if (
        task.is_recurring
        and task.due_date
        and task.recurrence_pattern
    ):
        next_due_date = get_next_due_date(
            task.due_date,
            task.recurrence_pattern,
            task.recurrence_interval or 1
        )
        if next_due_date and (not task.recurrence_end_date or next_due_date <= task.recurrence_end_date):
            new_task = Task(
                user_id=task.user_id,
                title=task.title,
                description=task.description,
                status=TaskStatus.pending,
                due_date=next_due_date,
                is_recurring=task.is_recurring,
                recurrence_pattern=task.recurrence_pattern,
                recurrence_interval=task.recurrence_interval,
                recurrence_end_date=task.recurrence_end_date,
            )
            db.add(new_task)
            db.commit()
            db.refresh(new_task)
            created_new = True

    return {
        "completed_task_id": str(task.id),
        "created_next_occurrence": created_new
    }

# Get tasks due by date/range and completed tasks within the same period
@router.get("/due", response_model=List[TaskOut])
def get_tasks_due(
    due_by: Optional[datetime] = Query(None),
    period: Optional[str] = Query(None, description="Filter period: today, week, month"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    try:
        # Then proceed with normal task fetching
        query = db.query(Task).filter(Task.user_id == user.id)
        
        if due_by and period:
            # For completed tasks, filter by completion date within the period
            if period == "today":
                start_of_day = datetime.combine(due_by.date(), datetime.min.time())
                end_of_day = datetime.combine(due_by.date(), datetime.max.time())
                query = query.filter(
                    or_(
                        # Pending tasks due by the end of day
                        and_(Task.status == TaskStatus.pending, Task.due_date <= end_of_day),
                        # Completed tasks completed today
                        and_(Task.status == TaskStatus.completed, 
                             Task.completed_at >= start_of_day, 
                             Task.completed_at <= end_of_day)
                    )
                )
            elif period == "week":
                # Get start and end of week
                start_of_week = due_by - timedelta(days=due_by.weekday())
                start_of_week = datetime.combine(start_of_week.date(), datetime.min.time())
                end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
                
                query = query.filter(
                    or_(
                        # Pending tasks due by the end of week
                        and_(Task.status == TaskStatus.pending, Task.due_date <= end_of_week),
                        # Completed tasks completed this week
                        and_(Task.status == TaskStatus.completed, 
                             Task.completed_at >= start_of_week, 
                             Task.completed_at <= end_of_week)
                    )
                )
            elif period == "month":
                # Get start and end of month (30 days from now)
                start_of_month = due_by - timedelta(days=30)
                start_of_month = datetime.combine(start_of_month.date(), datetime.min.time())
                end_of_month = due_by + timedelta(days=30)
                end_of_month = datetime.combine(end_of_month.date(), datetime.max.time())
                
                query = query.filter(
                    or_(
                        # Pending tasks due by the end of month
                        and_(Task.status == TaskStatus.pending, Task.due_date <= end_of_month),
                        # Completed tasks completed this month
                        and_(Task.status == TaskStatus.completed, 
                             Task.completed_at >= start_of_month, 
                             Task.completed_at <= end_of_month)
                    )
                )
        elif due_by:
            # Legacy behavior - only filter by due date
            query = query.filter(Task.due_date <= due_by)
        
        return query.order_by(Task.due_date).all()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tasks: {str(e)}")




@router.get("/", response_model=List[TaskOut])
def get_all_tasks(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Get all tasks"""
    try:
        # Then return the tasks
        return app.crud.task.get_all_tasks(db)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tasks: {str(e)}")

# @router.get("/{task_id}", response_model=TaskOut)
# def get_task(task_id: UUID, db: Session = Depends(get_db)):
#     db_task = app.crud.task.get_task(db, task_id)
#     if not db_task:
#         raise HTTPException(status_code=404, detail="Task not found")
#     return db_task


@router.put("/{task_id}", response_model=TaskOut)
def update_task(task_id: UUID, task_update: TaskUpdate, db: Session = Depends(get_db)):
    db_task = app.crud.task.update_task(db, task_id, task_update)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: UUID, db: Session = Depends(get_db)):
    success = app.crud.task.delete_task(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return None




@router.post("/create-from-text", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task_from_text(
    user_input: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Create a task from natural language input"""
    try:
        # Get current datetime in EST timezone
        est_tz = pytz.timezone('America/New_York')
        current_datetime = datetime.now(est_tz)
        
        # Analyze the user input with current datetime context
        analysis = analyze_task_input(user_input, current_datetime)
        
        # Create task data
        task_data = TaskCreate(
            title=analysis["title"],
            description=analysis["description"],
            due_date=datetime.fromisoformat(analysis["due_date"]) if analysis["due_date"] else None,
            preferred_time=datetime.strptime(analysis["preferred_time"], "%H:%M").time() if analysis["preferred_time"] else None,
            is_recurring=analysis["is_recurring"],
            recurrence_pattern=analysis["recurrence_pattern"],
            recurrence_interval=analysis["recurrence_interval"],
            recurrence_end_date=datetime.fromisoformat(analysis["recurrence_end_date"]) if analysis["recurrence_end_date"] else None,
        )
        
        # Create task in database
        task = app.crud.task.create_task(db, task_data, user_id=user.id)
        
        # Schedule in Google Calendar
        calendar_service = GoogleCalendarService()
        
        # Determine start time with timezone conversion
        if analysis["preferred_time"]:
            # Use specified time
            start_time = datetime.strptime(analysis["preferred_time"], "%H:%M")
            
            # Handle timezone conversion first
            if analysis.get("timezone"):
                # Convert from specified timezone to local timezone
                source_tz = pytz.timezone(analysis["timezone"])
                local_tz = pytz.timezone('America/New_York')  # Your local timezone
                
                # Determine the target date
                if analysis["due_date"]:
                    target_date = datetime.fromisoformat(analysis["due_date"])
                else:
                    # If no due date, use today
                    target_date = datetime.now()
                
                # Create the full datetime in the source timezone
                start_time = source_tz.localize(start_time.replace(
                    year=target_date.year,
                    month=target_date.month,
                    day=target_date.day
                ))
                
                # Convert to local timezone
                start_time = start_time.astimezone(local_tz)
                
                # Debug logging
                print(f"Debug - Source time: {analysis['preferred_time']} in {analysis['timezone']}")
                print(f"Debug - Converted to local: {start_time}")
                print(f"Debug - Current local time: {datetime.now(local_tz)}")
                print(f"Debug - Target date: {target_date}")
                print(f"Debug - Converted date: {start_time.date()}")
                
                # If the user specified "today" but the converted time is on a different date,
                # we need to adjust the date to match the user's intent
                if analysis["due_date"]:
                    # User specified a specific date, so we need to ensure the converted time
                    # is on that same date in the local timezone
                    target_date_local = local_tz.localize(target_date.replace(hour=0, minute=0, second=0, microsecond=0))
                    
                    # If the converted time is on a different date than intended, adjust it
                    if start_time.date() != target_date.date():
                        print(f"Debug - Date mismatch: intended {target_date.date()}, got {start_time.date()}")
                        # Adjust the time to be on the intended date
                        start_time = start_time.replace(
                            year=target_date.year,
                            month=target_date.month,
                            day=target_date.day
                        )
                        print(f"Debug - Adjusted start time: {start_time}")
                
                # Check if the final time is in the past for today
                now = datetime.now(local_tz)
                if start_time.date() == now.date() and start_time < now:
                    print(f"Debug - Scheduling for tomorrow because {start_time} < {now}")
                    tomorrow = now + timedelta(days=1)
                    start_time = start_time.replace(
                        year=tomorrow.year,
                        month=tomorrow.month,
                        day=tomorrow.day
                    )
                    print(f"Debug - New start time: {start_time}")
            else:
                # No timezone specified, assume local time
                if analysis["due_date"]:
                    start_time = start_time.replace(
                        year=datetime.fromisoformat(analysis["due_date"]).year,
                        month=datetime.fromisoformat(analysis["due_date"]).month,
                        day=datetime.fromisoformat(analysis["due_date"]).day
                    )
                else:
                    # If no due date, use today
                    start_time = start_time.replace(
                        year=datetime.now().year,
                        month=datetime.now().month,
                        day=datetime.now().day
                    )
                
                # Check if the time is in the past for today
                now = datetime.now()
                if not analysis["due_date"] and start_time < now:
                    # If no specific date and time is in the past, schedule for tomorrow
                    tomorrow = now + timedelta(days=1)
                    start_time = start_time.replace(
                        year=tomorrow.year,
                        month=tomorrow.month,
                        day=tomorrow.day
                    )
                
                local_tz = pytz.timezone('America/New_York')
                start_time = local_tz.localize(start_time)
        else:
            # Find available slot
            if analysis["due_date"]:
                target_date = datetime.fromisoformat(analysis["due_date"])
            else:
                # If no due date, use today
                target_date = datetime.now()
            
            available_slots = calendar_service.find_available_slots(target_date)
            if available_slots:
                start_time = available_slots[0]  # First available slot
            else:
                # Fallback to 11 AM
                start_time = target_date.replace(hour=11, minute=0, second=0, microsecond=0)
        
        # Create recurrence rule if needed
        recurrence_rule = None
        if analysis["is_recurring"] and analysis["recurrence_pattern"]:
            if analysis["recurrence_pattern"] == "daily":
                recurrence_rule = f"RRULE:FREQ=DAILY;INTERVAL={analysis['recurrence_interval'] or 1}"
                if analysis["recurrence_end_date"]:
                    end_date = datetime.fromisoformat(analysis["recurrence_end_date"])
                    recurrence_rule += f";UNTIL={end_date.strftime('%Y%m%d')}"
            elif analysis["recurrence_pattern"] == "weekly":
                recurrence_rule = f"RRULE:FREQ=WEEKLY;INTERVAL={analysis['recurrence_interval'] or 1}"
            elif analysis["recurrence_pattern"] == "monthly":
                recurrence_rule = f"RRULE:FREQ=MONTHLY;INTERVAL={analysis['recurrence_interval'] or 1}"
        
        # Create calendar event using task title and description
        calendar_event = calendar_service.create_event(
            title=task.title,
            description=task.description or "",
            start_time=start_time,
            duration_minutes=analysis.get("duration_minutes", 60),
            recurring=analysis["is_recurring"],
            recurrence_rule=recurrence_rule
        )
        
        # Update the task with the actual scheduled time and calendar event ID
        if calendar_event and 'id' in calendar_event:
            # Extract the actual scheduled time from the calendar event
            scheduled_time = start_time.time()
            
            # Update the task's preferred_time and calendar_event_id
            task.preferred_time = scheduled_time
            task.calendar_event_id = calendar_event['id']
            
            # Save the updated task
            db.commit()
            db.refresh(task)
        
        return task
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.post("/reschedule-expired", response_model=List[dict])
def reschedule_expired_calendar_events_endpoint(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = GoogleCalendarService()
    results = service.reschedule_expired_calendar_events(user_id=user.id, db=db)
    return results