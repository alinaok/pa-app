import os
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import pytz
from sqlalchemy.orm import Session
from app.models.task import Task
from sqlalchemy import and_

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarService:
    def __init__(self, timezone_str: str = 'America/New_York'):
        self.service = None
        self.timezone_str = timezone_str
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        creds = None
        
        # Load existing credentials
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                # Use the exact redirect URI that matches Google Cloud Console
                flow.redirect_uri = 'http://localhost:9090/oauth2callback'
                creds = flow.run_local_server(port=9090)
            
            # Save credentials
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('calendar', 'v3', credentials=creds)
    
    # List ALL available slots on ONE specific date
    def find_available_slots(self, date: datetime, duration_minutes: int = 60, start_hour: int = 11, end_hour: int = 21) -> List[datetime]:
        """Find available time slots for a given date with flexible hours"""
        # Make sure date is timezone-aware
        if date.tzinfo is None:
            user_tz = pytz.timezone(self.timezone_str)
            date = user_tz.localize(date)
        
        # Ensure start_hour and end_hour are within valid range
        start_hour = max(0, min(23, start_hour))
        end_hour = max(0, min(23, end_hour))
        
        start_of_day = date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=end_hour, minute=59, second=59, microsecond=999999)
        
        # Get existing events for the day
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=start_of_day.isoformat(),
            timeMax=end_of_day.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Find gaps between events
        available_slots = []
        current_time = start_of_day
        
        for event in events:
            event_start_str = event['start'].get('dateTime', event['start'].get('date'))
            event_start = datetime.fromisoformat(event_start_str)
            
            if event_start.tzinfo is None:
                user_tz = pytz.timezone(self.timezone_str)
                event_start = user_tz.localize(event_start)
            
            # Check if there's enough time before this event
            if (event_start - current_time).total_seconds() / 60 >= duration_minutes:
                available_slots.append(current_time)
            
            # Move to end of this event
            event_end_str = event['end'].get('dateTime', event['end'].get('date'))
            event_end = datetime.fromisoformat(event_end_str)
            
            if event_end.tzinfo is None:
                user_tz = pytz.timezone(self.timezone_str)
                event_end = user_tz.localize(event_end)
            
            current_time = event_end
        
        # Check if there's time after the last event
        if (end_of_day - current_time).total_seconds() / 60 >= duration_minutes:
            available_slots.append(current_time)
        
        return available_slots

    # List the NEXT available slot across MULTIPLE days. Multiple days (up to 7 days ahead)
    def find_next_available_slot(self, after_time: datetime, duration_minutes: int = 60, 
                                max_days_ahead: int = 7) -> Optional[datetime]:
        """Find the next available slot after a given time"""
        current_time = after_time
        end_search = current_time + timedelta(days=max_days_ahead)
        
        while current_time < end_search:
            # Check current day
            available_slots = self.find_available_slots(
                current_time.date(), 
                duration_minutes,
                start_hour=max(current_time.hour, 11),  # Don't start before 11 AM
                end_hour=22
            )
            
            # Find first available slot after current time
            for slot in available_slots:
                if slot > current_time:
                    return slot
            
            # Move to next day
            current_time = (current_time + timedelta(days=1)).replace(hour=11, minute=0, second=0, microsecond=0)
        
        return None
    
    def create_event(self, title: str, description: str, start_time: datetime, 
                    duration_minutes: int = 60, recurring: bool = False,
                    recurrence_rule: Optional[str] = None) -> dict:
        """Create a Google Calendar event"""
        end_time = start_time + timedelta(minutes=duration_minutes) 
        
        # Make sure datetime objects are timezone-aware
        if start_time.tzinfo is None:
            user_tz = pytz.timezone(self.timezone_str)
            start_time = user_tz.localize(start_time)
        
        if end_time.tzinfo is None:
            user_tz = pytz.timezone(self.timezone_str)
            end_time = user_tz.localize(end_time)
        
        # Convert to UTC for Google Calendar API
        start_time_utc = start_time.astimezone(pytz.UTC)
        end_time_utc = end_time.astimezone(pytz.UTC)
        
        event = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_time_utc.isoformat(),
                'timeZone': self.timezone_str,
            },
            'end': {
                'dateTime': end_time_utc.isoformat(),
                'timeZone': self.timezone_str,
            },
        }
        
        if recurring and recurrence_rule:
            event['recurrence'] = [recurrence_rule]
        
        event = self.service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        
        return event
    
    def reschedule_expired_calendar_events(self, user_id: str, db: Session) -> List[dict]:
        try:
            user_tz = pytz.timezone(self.timezone_str)
            now = datetime.now(user_tz)

            def parse_dt(value: str) -> datetime:
                dt = datetime.fromisoformat(value)
                if dt.tzinfo is None:
                    return user_tz.localize(dt)
                return dt.astimezone(user_tz)

            def find_first_available_between(window_start: datetime, window_end: datetime, duration_minutes: int) -> Optional[datetime]:
                # Ensure timezone-aware bounds
                if window_start.tzinfo is None:
                    window_start = user_tz.localize(window_start)
                if window_end.tzinfo is None:
                    window_end = user_tz.localize(window_end)

                events_result = self.service.events().list(
                    calendarId='primary',
                    timeMin=window_start.astimezone(pytz.UTC).isoformat(),
                    timeMax=window_end.astimezone(pytz.UTC).isoformat(),
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                events = events_result.get('items', [])

                current = window_start
                for event in events:
                    es = event['start'].get('dateTime') or event['start'].get('date')
                    ee = event['end'].get('dateTime') or event['end'].get('date')
                    event_start = parse_dt(es)
                    event_end = parse_dt(ee)

                    # If there's enough time before this event
                    if (event_start - current).total_seconds() / 60 >= duration_minutes:
                        return current

                    # Move the cursor forward
                    if event_end > current:
                        current = event_end

                # Space after the last event
                if (window_end - current).total_seconds() / 60 >= duration_minutes:
                    return current

                return None

            # Pending tasks that have calendar events
            expired_tasks = db.query(Task).filter(
                and_(
                    Task.user_id == user_id,
                    Task.status == "pending",
                    Task.calendar_event_id.isnot(None)
                )
            ).all()

            rescheduled_events = []

            for task in expired_tasks:
                # Determine if the linked calendar event has already ended
                is_expired = False
                event = None
                try:
                    event = self.service.events().get(
                        calendarId='primary',
                        eventId=task.calendar_event_id
                    ).execute()
                except Exception:
                    event = None

                if event:
                    end_str = event['end'].get('dateTime') or event['end'].get('date')
                    if end_str:
                        event_end_local = parse_dt(end_str)
                        is_expired = event_end_local < now
                else:
                    # Fallback to original heuristic
                    is_expired = self._is_calendar_event_expired(task)

                if not is_expired:
                    continue

                duration = getattr(task, 'duration_minutes', None) or 60

                # Try today: from 2 hours from now until 9pm local time
                window_start = now + timedelta(hours=2)
                today_cutoff = now.replace(hour=21, minute=0, second=0, microsecond=0)

                slot = None
                if window_start < today_cutoff:
                    slot = find_first_available_between(window_start, today_cutoff, duration)

                # If no slot today, try tomorrow 11am–9pm
                if not slot:
                    tomorrow = now + timedelta(days=1)
                    tomorrow_start = tomorrow.replace(hour=11, minute=0, second=0, microsecond=0)
                    tomorrow_end = tomorrow.replace(hour=21, minute=0, second=0, microsecond=0)
                    slot = find_first_available_between(tomorrow_start, tomorrow_end, duration)

                if slot:
                    # Replace the calendar event, don't touch task's due_date/preferred_time
                    try:
                        self.service.events().delete(
                            calendarId='primary',
                            eventId=task.calendar_event_id
                        ).execute()
                    except Exception as e:
                        print(f"Warning: failed to delete old event {task.calendar_event_id}: {e}")

                    new_event = self.create_event(
                        title=task.title,
                        description=task.description or "",
                        start_time=slot,
                        duration_minutes=duration
                    )

                    task.calendar_event_id = new_event['id']
                    db.commit()

                    rescheduled_events.append({
                        "task_id": str(task.id),
                        "task_title": task.title,
                        "new_time": slot.isoformat()
                    })

            return rescheduled_events

        except Exception as e:
            print(f"Error rescheduling expired calendar events: {e}")
            return []

    def _is_calendar_event_expired(self, task: Task) -> bool:
        """Check if a task's calendar event time has passed"""
        if not task.preferred_time or not task.due_date:
            return False
        
        # Create datetime from due_date + preferred_time
        task_datetime = datetime.combine(task.due_date.date(), task.preferred_time)
        user_tz = pytz.timezone(self.timezone_str)
        task_datetime = user_tz.localize(task_datetime)
        
        now = datetime.now(user_tz)
        return task_datetime < now