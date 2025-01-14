import httplib2
import os
from datetime import datetime, timedelta
import yaml

from googleapiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from oauth2client import clientsecrets
from oauth2client.client import HttpAccessTokenRefreshError

from typing import Any, Optional

try:
    import argparse

    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at "C:\Users\user\.credentials\albert-heijn-calendar-sync.json"
SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Albert Heijn Calendar Sync'


class Calendar:
    @staticmethod
    def get_credentials() -> Any:
        """Gets valid user credentials from storage.
    
        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.
    
        Returns:
            Credentials, the obtained credential.
        """
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'albert-heijn-calendar-sync.json')

        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            try:
                flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
            except clientsecrets.InvalidClientSecretsError:
                print('Unable to locate client_secret.json. Please read the readme and make sure you have the' + \
                      ' file in the webscraper folder')
                exit()

            flow.user_agent = APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else:  # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials

    def __init__(self) -> None:
        """ Initializes the calendar by authenticating.

            Creates a Google Calendar API service object.
        """
        # Initialize a calendar connection.
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        self.service = discovery.build('calendar', 'v3', http=http)

        # Get the event bounds.
        # Get the current year and month
        current_date = datetime.now()
        current_week_start = current_date - timedelta(days=current_date.weekday())

        eight_weeks_ago_start_iso = (current_week_start - timedelta(weeks=8)).isoformat() + 'Z'  # 'Z' indicates UTC time
        four_weeks_later = (current_week_start + timedelta(weeks=4)).isoformat() + 'Z'  # 'Z' indicates UTC time
        
        # Debug
        #print(f"First of month is {firstofmonth}")
        #print(f"Last of month is {lastofmonth}")

        # Get this months events.
        try:
            events_result = self.service.events().list(
                calendarId='primary', timeMin=eight_weeks_ago_start_iso, timeMax=four_weeks_later, maxResults=84, singleEvents=True,
                orderBy='startTime').execute()
        except HttpAccessTokenRefreshError:
            print("Token has expired, please restart")
            raise RuntimeError
            
        # Save the events to check for duplicates later.
        self.events = events_result.get('items', [])
        
        # Open settings
        with open('settings.yaml') as s:
            settings = yaml.load(s, yaml.FullLoader)
        
        # Filter events to only have work events.
        self.events = [ev for ev in self.events if settings['description'] in ev.get('description', '')]

    def remove_duplicate_event(self, event: dict[str, Any]) -> None:
        """Removes duplicate events from the calendar

        :param event: JSON representation of the to be inserted event. For reference look at
            https://developers.google.com/google-apps/calendar/create-events
        """
        # Check if the event already exists.
        if not self.events:
            self.events = []  # Ensure self.events is initialized

        # Extract start datetime from event
        event_start_datetime_str = event['start']['dateTime']
        event_start_datetime = datetime.strptime(event_start_datetime_str, "%Y-%m-%dT%H:%M:%S%z")

        event_end_datetime_str = event['end']['dateTime']
        event_end_datetime = datetime.strptime(event_end_datetime_str, "%Y-%m-%dT%H:%M:%S%z")

        # Debug
        print(f"Trying to insert event: {event['summary']} at {event_start_datetime}")

        # Check if a similar event already exists
        for existing_event in self.events:
            existing_start_datetime_str = existing_event['start']['dateTime']
            existing_end_datetime_str = existing_event['end']['dateTime']

            existing_start_datetime = datetime.strptime(existing_start_datetime_str, "%Y-%m-%dT%H:%M:%S%z")
            existing_end_datetime = datetime.strptime(existing_end_datetime_str, "%Y-%m-%dT%H:%M:%S%z")
            
            # Perform comparison considering timezone differences
            if event_start_datetime == existing_start_datetime and event_end_datetime == existing_end_datetime:
                # Debug
                print(f"Event already exists: {event['summary']} at {event_start_datetime}")
                return  # Event already exists, do not insert
            else:
                # Debug
                print(f"No match: {event['summary']} at {event_start_datetime} vs {existing_event['summary']} at {existing_start_datetime}")

        # Insert event if not already present
        # Debug
        print(f"Inserting event: {event['summary']} at {event_start_datetime}")

        #self.service.events().insert(calendarId='primary', body=event).execute()

        # return all changed events
        return event


    def insert_event(self, event: dict[str, Any]) -> Optional[dict[str, Any]]:
        """ Inserts an event into the calendar.
        
            :param event: JSON representation of the to be inserted event. For reference look at
            https://developers.google.com/google-apps/calendar/create-events
            :return event: An event which needed to be inserted into the calender
        """

        # Check if the event already exists.
        if not self.events:
            self.events = []  # Ensure self.events is initialized

        # Extract start datetime from event
        event_start_datetime_str = event['start']['dateTime']
        event_start_datetime = datetime.strptime(event_start_datetime_str, "%Y-%m-%dT%H:%M:%S%z")

        event_end_datetime_str = event['end']['dateTime']
        event_end_datetime = datetime.strptime(event_end_datetime_str, "%Y-%m-%dT%H:%M:%S%z")

        # Debug
        print(f"Trying to insert event: {event['summary']} at {event_start_datetime}")

        # Check if a similar event already exists
        for existing_event in self.events:
            existing_start_datetime_str = existing_event['start']['dateTime']
            existing_end_datetime_str = existing_event['end']['dateTime']

            existing_start_datetime = datetime.strptime(existing_start_datetime_str, "%Y-%m-%dT%H:%M:%S%z")
            existing_end_datetime = datetime.strptime(existing_end_datetime_str, "%Y-%m-%dT%H:%M:%S%z")
            
            # Perform comparison considering timezone differences
            if event_start_datetime == existing_start_datetime and event_end_datetime == existing_end_datetime:
                # Debug
                print(f"Event already exists: {event['summary']} at {event_start_datetime}")
                return  # Event already exists, do not insert
            else:
                # Debug
                print(f"No match: {event['summary']} at {event_start_datetime} vs {existing_event['summary']} at {existing_start_datetime}")

        # Insert event if not already present
        # Debug
        print(f"Inserting event: {event['summary']} at {event_start_datetime}")

        #self.service.events().insert(calendarId='primary', body=event).execute()

        # return all changed events
        return event

        # TODO: update when schedule has changed

