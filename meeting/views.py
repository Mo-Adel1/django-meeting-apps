import json
import base64
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from datetime import datetime, timedelta
import pytz
import logging
import re

ACCOUNT_ID = settings.ACCOUNT_ID
CLIENT_ID = settings.CLIENT_ID
CLIENT_SECRET = settings.CLIENT_SECRET

TOKEN_URL = settings.TOKEN_URL
MEETING_URL = settings.MEETING_URL

logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'meeting/index.html')

def get_access_token():
    auth = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_auth = base64.b64encode(auth.encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"grant_type": "account_credentials", "account_id": ACCOUNT_ID}
    
    response = requests.post(TOKEN_URL, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception(f"Error fetching access token: {response.text}")

def generate_secure_password(length=8):
    import random
    import string
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

def validate_inputs(topic, agenda, duration, date_str, time_str, timezone):
    errors = []
    if not topic or len(topic) > 200:
        errors.append("Topic is required and cannot exceed 200 characters.")
    if not agenda or len(agenda) > 500:
        errors.append("Agenda is required and cannot exceed 500 characters.")
    if not duration or not duration.isdigit() or int(duration) < 10 or int(duration) > 1440:
        errors.append("Duration must be a number between 10 minutes and 1440 minutes (24 hours).")
    if not date_str or not re.match(r"\d{4}-\d{2}-\d{2}", date_str):
        errors.append("Date must be in YYYY-MM-DD format.")
    if not time_str or not re.match(r"\d{2}:\d{2}", time_str):
        errors.append("Time must be in HH:MM (24-hour) format.")
    if timezone not in pytz.all_timezones:
        errors.append("Invalid timezone provided.")
    return errors

def create_zoom_meeting(request):
    if request.method == 'POST':
        try:
            topic = request.POST.get('topic')
            date_str = request.POST.get('date')  # Expected format: YYYY-MM-DD
            time_str = request.POST.get('time')  # Expected format: HH:MM (24-hour format)
            duration = request.POST.get('duration')
            agenda = request.POST.get('agenda')
            timezone = request.POST.get('timezone', "Africa/Cairo")  # Default timezone
            
            # Validate inputs
            errors = validate_inputs(topic, agenda, duration, date_str, time_str, timezone)
            if errors:
                return JsonResponse({'errors': errors}, status=400)
            
            # Convert date and time to UTC
            local_timezone = pytz.timezone(timezone)
            local_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            local_datetime = local_timezone.localize(local_datetime)
            utc_datetime = local_datetime.astimezone(pytz.utc)
            
            # Ensure the date is in the future
            if utc_datetime <= datetime.now(pytz.utc) - timedelta(minutes=1):
                return JsonResponse({'error': 'Meeting time must be in the future'}, status=400)
            
            # Prepare Zoom meeting creation data
            meeting_data = {
                "topic": topic,
                "agenda": agenda,
                "type": 2,  # Scheduled meeting
                "start_time": utc_datetime.isoformat(),
                "duration": int(duration),
                "timezone": timezone,
                # "password": generate_secure_password(),  # Generate a secure password
                "settings": {
                    "host_video": True,
                    "participant_video": False,
                    "audio": "voip",
                    "auto_recording": "cloud",
                    "waiting_room": True,  # Enable waiting room
                    "join_before_host": False,  # Disable joining before host
                    "mute_upon_entry": True,  # Mute participants on entry
                    "approval_type": 2,  # Auto-approve registrants (for webinars)
                    "alternative_hosts": "",  # Add alternative hosts if needed
                    "closed_caption": True,  # Enable closed captioning
                    "registrants_email_notification": True  # Notify registrants via email
                },
                "tracking_fields": [
                    {"field": "Department", "value": "Marketing"},
                    {"field": "Event Name", "value": "Quarterly Review"}
                ]
            }
            
            # Step 2: Get Access Token
            access_token = get_access_token()
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
            
            # Make the API request to create the meeting
            response = requests.post(MEETING_URL, headers=headers, data=json.dumps(meeting_data))
            
            if response.status_code == 201:
                meeting_info = response.json()
                logger.info(f"Meeting created successfully: {meeting_info}")
                return JsonResponse({
                    'meeting_url': meeting_info['join_url'],
                    'start_time': meeting_info['start_time'],
                    'agenda': meeting_info['agenda'],
                    'password': meeting_info['password']
                })
            elif response.status_code == 400:
                error_message = response.json().get('message', 'Bad Request')
                logger.error(f"Bad Request: {error_message}")
                return JsonResponse({'error': error_message}, status=400)
            elif response.status_code == 404:
                logger.error("User does not exist.")
                return JsonResponse({'error': 'User does not exist.'}, status=404)
            elif response.status_code == 429:
                logger.error("Too many requests, please try again later.")
                return JsonResponse({'error': 'Too many requests, please try again later.'}, status=429)
            else:
                logger.error(f"Unexpected error: {response.text}")
                return JsonResponse({'error': 'An unexpected error occurred.'}, status=response.status_code)
        
        except Exception as e:
            logger.error(f"Error creating meeting: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)
