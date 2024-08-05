from google.oauth2 import service_account
from googleapiclient.discovery import build
from .models import Appointment

def create_google_calendar_event(appointment):
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    SERVICE_ACCOUNT_FILE = 'path/to/service_account.json'
    
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('calendar', 'v3', credentials=credentials)
    
    event = {
        'summary': f'Appointment with Dr. {appointment.doctor.get_full_name()}',
        'description': f'Speciality: {appointment.speciality}',
        'start': {
            'dateTime': f"{appointment.appointment_date}T{appointment.start_time.isoformat()}",
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': f"{appointment.appointment_date}T{appointment.end_time.isoformat()}",
            'timeZone': 'Asia/Kolkata',
        },
        'attendees': [
            {'email': appointment.doctor.email},
            {'email': appointment.patient.email},
        ],
    }
    
    event = service.events().insert(calendarId='primary', body=event).execute()
    return event['id']
