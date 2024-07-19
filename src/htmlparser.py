# encoding: utf-8

from bs4 import BeautifulSoup
import yaml
from datetime import datetime
import pyrfc3339 as rfc
import pytz
import json


class Parser:

    def block_to_json(self, html, month, year):
        """
        info index information:
        0 = day number      e.g. 19
        1 = start - end     e.g. (18:00 - 21:00) AH 152218:00 ~ 21:00geautoriseerd
        2 = start date      e.g. 18:00
        3 = end date        e.g. 21:00

        :param html: Html text that contains the information from ah.get_blocks()
        :param month: as 3 lettered string e.g. 'Apr'
        :param year: as 4 digit int.
        :return: json representation of the html.
        """
        soup = BeautifulSoup(str(html), 'html.parser')
        # Check if we have the correct block
        if not any(w in html for w in ['calendarCellRegularPast', 'calendarCellRegularFuture']):
            return None

        # Remove spaces
        info = [span.text.replace('\t', '').replace('\n', '') for span in soup.find_all('span')]

        # Convert the dates
        year = int(year)
        # TODO: carry over to next month
        month = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dec"].index(month[:3])
        day = int(info[0])
        # TODO: clean this up if possible
        starthour, startmin = [int(x) for x in info[2].split(":")]
        endhour, endmin = [int(x) for x in info[3].split(":")]

        # Generate RFC-3339 dates
        # TODO: clean this up if possible
        startdate = rfc.generate(self.timezone.localize(datetime(year, month, day, starthour, startmin)), utc=False)
        enddate = rfc.generate(self.timezone.localize(datetime(year, month, day, endhour, endmin)), utc=False)

        json_string = self.jsonformat.replace('_start', startdate).replace('_end', enddate)

        try:
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e}")
            print(f"Invalid JSON: {json_string}")
            return None

    def __init__(self):
        """
        Initialized the parser by creaing the json format
        and initializing the timezone.
        """
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
            .replace('_description', settings['description'])\
            .replace('_location', settings['location'])\
            .replace('_reminder', str(settings['reminder']))\
            .replace('_colorId', str(settings['colorId']))

        # Set the timezone.
        self.timezone = pytz.timezone(settings['timezone'])
