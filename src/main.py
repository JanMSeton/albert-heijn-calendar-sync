#!/usr/bin/env python

from googlecalendar import Calendar
from albertheijn import AlbertHeijn
from htmlparser import Parser
from emailer import Email
from datetime import datetime

def main():

    # Create scraper objects.
    ah = AlbertHeijn()
    parser = Parser()
    
    # Convert all blocks to json format.
    json = filter(None, [parser.block_to_json(element, ah.get_month(), ah.get_year()) for element in ah.get_schedule_blocks()])
    #sfilename = "https___sam.ahold.com_etm_time_timesheet_etmTnsMonth.jsp.html"
    #json = filter(None, [parser.block_to_json(element, ah.local_get_month(filename), ah.local_get_year(filename)) for element in ah.local_get_blocks(filename)])

    # Send new schedule week to email
    email = Email()
    email.send_email(json)
    ah.dispose()
    return
    calendar = Calendar()
    print('Updating calendar...')
    for event in json:
        calendar.insert_event(event)
    
    print('Done')

if __name__ == "__main__":
    main()

    


