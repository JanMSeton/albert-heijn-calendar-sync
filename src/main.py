#!/usr/bin/env python

from googlecalendar import Calendar
from albertheijn import AlbertHeijn
from htmlparser import Parser
from emailer import Email

def main():
    # Create scraper objects.
    ah = AlbertHeijn()
    parser = Parser()

    
    with open("tabletest.html", 'w') as file: # empty file
        pass

    json = (
        result
        for block in ah.get_table_list()
        for result in parser.pre_parse_table_by_team(block['table_html'], block['date_html'], ah.get_year())
        if result is not None
    )



    # Convert all blocks to json format.
    #json = filter(None, [parser.block_to_json(element, ah.get_month(), ah.get_year()) for element in ah.get_schedule_blocks()])
    # ah.dispose()
    # Send new schedule week to email
    email = Email()
    email.send_email(json)
    ah.dispose()

    # calendar = Calendar()
    # print('Updating calendar...')
    # for event in json:
    #     calendar.insert_event(event)

    # ah.dispose()
    
    # print('Done')

if __name__ == "__main__":
    main()

    


