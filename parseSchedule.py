from __future__ import print_function
import datetime
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import re
import dateutil.parser

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    timeNowUTC = datetime.datetime.utcnow()
    todayStart = timeNowUTC.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
    tomorrowEnd = timeNowUTC + datetime.timedelta(days=1)
    tomorrowEnd = tomorrowEnd.replace(hour=23,minute=59, second=59).isoformat() + 'Z'
    events = []
    events_result = service.events().list(calendarId='u61evjfscniu614cra1mt85r14@group.calendar.google.com', timeMin=todayStart, timeMax=tomorrowEnd, singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])
    schedule_content = ""

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        match = re.search(r"PID:([a-z0-9\-]+)",event['description'])
        pid = match.group(1)
        expected_file_name = dateutil.parser.isoparse(start).strftime('%Y%m%d_%H%M') + "_" + pid
        if "TYPE:RECORDED" in event['description']:    
            schedule_content = schedule_content + "\"" + start + "\",\"" + end + "\",\"" + pid + "\",\"" + expected_file_name + "\",\"" + event['summary'] + "\"\n"
    
    cron = open("/home/ubuntu/schedule.csv","w")
    cron.write(schedule_content)
    cron.close()


if __name__ == '__main__':
    main()