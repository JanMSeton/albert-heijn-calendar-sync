# encoding: utf-8

from bs4 import BeautifulSoup
import yaml
from datetime import datetime, timedelta
import pyrfc3339 as rfc
import pytz
import json
from typing import Optional, Any, Generator

VALIDWORKSTRINGS = {"Meeruren", "Gewerkte uren", "Betaalde pauze", "Onbetaalde pauze"}
WORKCODENAMEDICT = {
    "AGF": "AGF",
    "": "Werk",
    "CODG": "Codeboek gekoeld",
    "BRK-PD": "Betaalde pauze",
    "BRK-U/PD": "Onbetaalde pauze",
    "NAVU": "Navulling",
    "LA-LO": "Laden en lossen",
    "01": "Werk",
    "BAK": "Bakken",
    "OPZET": "Opzetten"
}

TEAMCODEDICT = {
    "OPERATIE": "Operatie",
    "VERS": "Vers"
}


class Parser:
        
    def pre_parse_table_by_team(self, table_html: str, day_html: str, year: str) -> Generator[dict[str, Any], None, None]:
        """
        Pre-process the HTML table to split by team and return JSON objects for each team if no "pauze" in description.
        """
        soup = BeautifulSoup(str(table_html), 'html.parser')
        table = soup.find('table')
        if table is None:
            # Log or handle the error if the table is not found
            print("Error: No table found in the provided HTML in the pre-parser.")
            return None 
    
        rows: list[list[str]] = [[col.get_text(strip=True) for col in row.find_all('td')]
                 for row in table.find_all('tr')[1:]]
        if not rows:
            print("No rows found in the table")
            return None

        current_team = ""
        team_rows: dict[str, list[list[str]]] = {}

        for row in rows:
            if len(row) < 8:
                continue  # Skip incomplete rows

            description = row[0]
            team = row[5]

            if 'pauze' not in description:
                if team != current_team:
                    if current_team:
                    # Process and store data for the previous team if it has valid rows
                        # Debug: Print team_rows for the previous team
                        print(f"Yielding data for team {current_team}: {team_rows.get(current_team, [])}")
                        yield self.team_table_to_json(team_rows.get(current_team, []), day_html, year)

                    # Initialize new team
                    current_team = team
                    team_rows[current_team] = [row]  # Start with the current row
                else:
                    team_rows[current_team].append(row)  # Continue adding rows to the current team
            else:
                team_rows[current_team].append(row)

        # Handle the last team
        if current_team:
            # Debug: Print team_rows for the previous team
            print(f"Yielding data for team {current_team}: {team_rows.get(current_team, [])}")
            yield self.team_table_to_json(team_rows.get(current_team, []), day_html, year)


    def team_table_to_json(self, rows: list[list[str]], day_html: str, year: str) -> Optional[dict[str, Any]]:

        if not rows:
            print("No rows found")
            return None
        else:
            # Debug: Print rows to verify data
            print(f"Processing rows at start: {rows}")


        with open("tabletest.html", 'a') as file:
            file.write("Day html:" + str(day_html) + "\n" +str(rows) + "\n")
        
        year = int(year)

        # Split day_html to extract the day
        date_parts = str(day_html).split()
        day = int(date_parts[1].strip(','))
        month = str(date_parts[0])

        # Ensure `month` is an integer, assuming it's provided as an integer directly (e.g., 7 for July)
        if isinstance(month, str):
            month = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dec"].index(month[:3])
        elif not (1 <= month <= 12):
            raise ValueError("Month must be between 1 and 12")

        description_str = ""
        pauze_onbetaald = timedelta()
        pauze_betaald = timedelta()
        pauze_tijd = timedelta()
        earliest_start = None
        latest_end = None
        contains_shift = False

        for row in rows:
            contains_shift = False
            if len(row) < 8:
                continue  # Skip incomplete rows

            description = row[0]
            start_time = row[2]
            end_time = row[3]
            duration = row[4]
            team = row[5]
            activity = row[6] 

            # Check if the description contains "Toeslaguren 50" or "Toeslaguren 100"
            if description not in VALIDWORKSTRINGS:
                continue  # Skip this row

            contains_shift = True
            # Create the start and end datetime objects
            start_hour, start_minute = map(int, start_time.split(":"))
            end_hour, end_minute = map(int, end_time.split(":"))

            start_datetime = self.timezone.localize(datetime(year, month, day, start_hour, start_minute), is_dst=None)
            end_datetime = self.timezone.localize(datetime(year, month, day, end_hour, end_minute), is_dst=None)

            # Determine the earliest start time
            if earliest_start is None or start_datetime < earliest_start:
                earliest_start = start_datetime

            # Determine the latest end time
            if latest_end is None or end_datetime > latest_end:
                latest_end = end_datetime

            if 'pauze' in description:
                # Split the duration string into hours and minutes
                hours, minutes = map(int, duration.split(':'))
                # Create a timedelta object for the current duration
                pauze_tijd = timedelta(hours=hours, minutes=minutes)
                if 'Onbetaalde pauze' in description :
                    # Add the current duration to the total
                    pauze_onbetaald += pauze_tijd
                else:
                    pauze_betaald += pauze_tijd

            description_str += f"Team: {TEAMCODEDICT.get(team, team)}, Activiteit: {WORKCODENAMEDICT.get(activity, activity)}\n"

        if not contains_shift: return None # The page did not conatains a shit, only for example an Absence message

        # Generate RFC-3339 dates
        # TODO: clean this up if possible
        earliest_start_str = rfc.generate(earliest_start.astimezone(self.timezone), utc=False) if earliest_start else ''
        latest_end_str = rfc.generate(latest_end.astimezone(self.timezone), utc=False) if latest_end else ''
        # Convert the total pauze durations to strings
        pauze_onbetaald_str = self._timedelta_to_str(pauze_onbetaald)
        pauze_betaald_str = self._timedelta_to_str(pauze_betaald)

        description_str += f"Pauze (Onbetaald): {pauze_onbetaald_str}, Pauze (Betaald): {pauze_betaald_str}\n Event gemaakt door albert-heijn-calender-sync"
        description_str = description_str.replace('\n', '\\n') # Fixes JSON

        # Replace placeholders in your JSON format string (assumed)
        json_string = self.jsonformat.replace('_start', earliest_start_str).replace('_end', latest_end_str).replace('_description', description_str)

        try:
            print(f"json_string : {json_string}")
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}")
            print(f"Invalid JSON: {json_string}")
            return None

    def _timedelta_to_str(self, td: timedelta) -> str:
        """Convert a timedelta object to a string in 'H:M:S' format."""
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}:{minutes:02}"
        

    def __init__(self) -> None:
        """
        Initialized the parser by creaing the json format
        and initializing the timezone.
        """
        print("Initializing parser...")
        with open('settings.yaml') as s:
            settings = yaml.load(s, yaml.FullLoader)

        # Json format for google calendar.
        self.jsonformat = '''{
            "summary":"_summary",
            "location":"_location",
            "description":"_description",
            "start": {
                "dateTime":"_start"
            },
            "end": {
                "dateTime":"_end"
            },
            "reminders": {
                "useDefault": false,
                "overrides":[
                    {
                        "method":"popup",
                        "minutes":_reminder
                    }
                ]
            },
            "colorId": "_colorId"
        }'''

        # Replace default values with user settings.
        self.jsonformat = self.jsonformat.replace('_summary', settings['summary'])\
            .replace('_location', settings['location'])\
            .replace('_reminder', str(settings['reminder']))\
            .replace('_colorId', str(settings['colorId']))

        # Set the timezone.
        self.timezone = pytz.timezone(settings['timezone'])
