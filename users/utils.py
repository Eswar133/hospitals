# utils.py

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from icalendar import Calendar, Event, vCalAddress, vText
from datetime import datetime 
from django.core.files.base import ContentFile
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
import io
from ics import Calendar, Event
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.views import View
from django.template.loader import render_to_string
from .models import Appointment, User


def create_ics_file(appointment):
    # Create a calendar instance
    cal = Calendar()

    # Create an event instance
    event = Event()
    event.name = f"Appointment with Dr. {appointment.doctor.get_full_name()}"
    event.begin = datetime.combine(appointment.appointment_date, appointment.start_time).isoformat()
    event.end = datetime.combine(appointment.appointment_date, appointment.end_time).isoformat()
    event.description = f"Speciality: {appointment.speciality}"

    # Add event to the calendar
    cal.events.add(event)

    # Create a file-like object to store the .ics content
    ics_file = io.BytesIO()
    ics_file.write(str(cal).encode('utf-8'))
    ics_file.seek(0)  # Rewind the file pointer to the beginning

    return ics_file

class BookAppointmentView(View):
    def get(self, request, pk):
        doctor = get_object_or_404(User, pk=pk, user_type='doctor')
        return render(request, 'book_appointment.html', {'doctor': doctor})

    def post(self, request, pk):
        doctor = get_object_or_404(User, pk=pk, user_type='doctor')
        speciality = request.POST.get('speciality')
        appointment_date = request.POST.get('appointment_date')
        start_time = request.POST.get('start_time')

        if not all([speciality, appointment_date, start_time]):
            return JsonResponse({'error': 'All fields are required.'}, status=400)

        # Parse the appointment date and start time
        appointment_date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        start_time_obj = datetime.strptime(start_time, '%H:%M').time()
        appointment_datetime_naive = datetime.combine(appointment_date_obj, start_time_obj)

        # Convert the naive datetime to an aware datetime
        appointment_datetime = timezone.make_aware(appointment_datetime_naive, timezone.get_current_timezone())

        # Check if the appointment datetime is in the past
        if appointment_datetime <= timezone.now():
            return JsonResponse({'error': 'Cannot book an appointment in the past.'}, status=400)

        end_time = (appointment_datetime + timedelta(minutes=45)).time()

        appointment = Appointment.objects.create(
            patient=request.user,
            doctor=doctor,
            speciality=speciality,
            appointment_date=appointment_datetime.date(),
            start_time=appointment_datetime.time(),
            end_time=end_time
        )

        # Send email confirmation
        self.send_appointment_email(appointment)

        return JsonResponse({'message': 'Appointment booked successfully!'})

    def send_appointment_email(self, appointment):
        current_site = get_current_site(self.request)
        mail_subject = 'Appointment Confirmation'
        message = render_to_string('appointment_email.html', {
            'user': self.request.user,
            'doctor': appointment.doctor,
            'speciality': appointment.speciality,
            'date': appointment.appointment_date,
            'start_time': appointment.start_time,
            'end_time': appointment.end_time,
        })
        event_details = {
            'summary': f'Appointment with Dr. {appointment.doctor.get_full_name()}',
            'start': datetime.combine(appointment.appointment_date, appointment.start_time),
            'end': datetime.combine(appointment.appointment_date, appointment.end_time),
            'attendee_name': self.request.user.get_full_name()
        }

        send_email_with_calendar_invite(
            to_email=appointment.patient.email,
            subject=mail_subject,
            message=message,
            event_details=event_details
        )

def create_google_calendar_event(appointment):
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    SERVICE_ACCOUNT_FILE = 'google_calendar_credentials.json'
    
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

def send_email_with_calendar_invite(to_email, subject, message, event_details):
    from_email = 'manikantapadala358@gmail.com'
    password = 'btoi uqai hosw upxz'
    
    msg['Content-class'] = 'urn:content-classes:calendarmessage'
    msg['Content-Type'] = 'text/calendar; method=REQUEST'


    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'html'))

    # Create the calendar invite
    cal = Calendar()
    cal.add('prodid', '-//My calendar product//mxm.dk//')
    cal.add('version', '2.0')

    event = Event()
    event.add('summary', event_details['summary'])
    event.add('dtstart', event_details['start'])
    event.add('dtend', event_details['end'])
    event.add('dtstamp', datetime.now())
    event.add('uid', f'{event_details["start"].timestamp()}@example.com')
    event.add('priority', 5)

    organizer = vCalAddress(f'MAILTO:{from_email}')
    organizer.params['cn'] = vText('Organizer Name')
    organizer.params['role'] = vText('REQ-PARTICIPANT')
    event['organizer'] = organizer

    attendee = vCalAddress(f'MAILTO:{to_email}')
    attendee.params['cn'] = vText(event_details['attendee_name'])
    attendee.params['role'] = vText('REQ-PARTICIPANT')
    event.add('attendee', attendee)

    cal.add_component(event)

    ical_content = cal.to_ical()
    part = MIMEApplication(ical_content, 'octet-stream')
    part.add_header('Content-Disposition', 'attachment; filename="appointment.ics"')
    msg.attach(part)

    # Send the email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")
    from_email = 'manikantapadala358@gmail.com'
    password = 'btoi uqai hosw upxz'

    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'html'))

    cal = Calendar()
    cal.add('prodid', '-//My calendar product//mxm.dk//')
    cal.add('version', '2.0')

    event = Event()
    event.add('summary', event_details['summary'])
    event.add('dtstart', event_details['start'])
    event.add('dtend', event_details['end'])
    event.add('dtstamp', datetime.now())
    event.add('uid', f'{event_details["start"].timestamp()}@example.com')
    event.add('priority', 5)
    event.add('organizer', f'MAILTO:{from_email}')
    event.add('attendee', f'MAILTO:{to_email}')

    cal.add_component(event)

    ical_content = cal.to_ical()
    part = MIMEApplication(ical_content, 'octet-stream')
    part.add_header('Content-Disposition', 'attachment; filename="invite.ics"')
    msg.attach(part)

    # Send the email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")