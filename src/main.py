#!/usr/bin/env python

from googlecalendar import Calendar
from albertheijn import AlbertHeijn
from htmlparser import Parser
from emailer import Email

def main():
    # Create scraper objects.
    ah = AlbertHeijn()
    parser = Parser()

    
    with open("tabletest.html", 'w') as file: # empty the file
        pass

    json = [
        result
        for block in ah.get_table_list()
        for result in parser.pre_parse_table_by_team(block['table_html'], block['date_html'], ah.get_year())
        if result is not None
    ]



    # Send new schedule week to email
    # email = Email()
    # email.send_email(*email.two_weeks_from_now, json)
    ah.dispose()

    calendar = Calendar()
    changed_events = []
    print('Updating calendar...')
    for event in json:
        if calendar.insert_event(event):
            changed_events.append(event)

    # send changed schedule weeks to email
    # email.send_changed_weeks_email(changed_events, json)

    ah.dispose()
    
    print('Done')

if __name__ == "__main__":
    main()

    


