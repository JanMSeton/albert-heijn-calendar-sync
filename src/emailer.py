#!/usr/bin/env python


from datetime import datetime, timedelta
import pytz
import yaml
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
class Email:

    def __init__(self, mode = 'default'):

        self.mode = mode
        if mode != 'default':
            return

        with open('settings.yaml') as s:
                settings = yaml.load(s, yaml.FullLoader)
        
        # Email credentials and SMTP server configuration
        self.from_email = str(settings['your_email'])
        self.to_email = str(settings['send_to_email'])
        self.password = str(settings['your_email_password'])
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.timezone = pytz.timezone(settings['timezone'])


    def send_email(self, json):

        if self.mode != 'default':
            return

        body = self.__generate_schedule_table__(json)
        subject = "WERKEN"

        # Create a MIME object
        msg = MIMEMultipart()
        msg['From'] = self.from_email
        msg['To'] = self.to_email
        msg['Subject'] = subject

        # Attach the body with the msg instance
        msg.attach(MIMEText(body, 'html'))

        try:
            # Create an SMTP session
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Secure the connection
            server.login(self.from_email, self.password)  # Login to the email account
            text = msg.as_string()  # Convert the MIME object to a string
            server.sendmail(self.from_email, self.to_email, text)  # Send the email
            print("Email sent successfully!")
        except Exception as e:
            print(f"Failed to send email: {e}")
        finally:
            server.quit()  # Terminate the SMTP session


    def __generate_schedule_table__(self, json):
        with open('settings.yaml') as s:
            settings = yaml.load(s, yaml.FullLoader)

        # Get the current date
        current_date = datetime.now()

        # Calculate the start of the current week (Monday)
        current_week_start = current_date - timedelta(days=current_date.weekday())

        # Calculate the first Monday of the second week after the current one
        second_week_monday = current_week_start + timedelta(weeks=2)

        year = second_week_monday.year
        month = second_week_monday.month
        week_number = second_week_monday.isocalendar()[1] 

        # Calculate the end of the week (Sunday)
        end_of_week = second_week_monday + timedelta(days=6)

        # Debug
        #print("The first Monday of the third week after the current one is:", second_week_monday.strftime("%Y-%m-%d"))
        #print("The end of that week is:", end_of_week.strftime("%Y-%m-%d"))

        # Prepare the HTML for the schedule table
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                table {{
                    border-collapse: collapse;
                    width: 100%;
                }}
                th, td {{
                    border: 1px solid black;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
            </style>
        </head>
        <body>
            <h2>Schedule for {} {} - Week {}</h2>
            <table>
                <tr>
                    <th>Date</th>
                    <th>Title</th>
                    <th>Time</th>
                    <th>Duration</th>
                </tr>
        '''.format(datetime(year, month, 1).strftime('%B'), year, week_number)

        # Flag to check if any event has been added
        events_found = False

        # Add rows for all schedule entries matching the current day
        for event in json:
            events_found = True
            # Iterate over every day of the week starting at second_week monday
            day = second_week_monday
            start_datetime = datetime.fromisoformat(event['start']['dateTime'])
            end_datetime = datetime.fromisoformat(event['end']['dateTime'])

            while day <= end_of_week:
                if start_datetime.date().isoformat() == day.date().isoformat():
                    
                    event_time_formatted = f"{start_datetime.strftime('%H:%M')} - {end_datetime.strftime('%H:%M')}"
                    #print(f"Event looks like: {event_time_str}")  # Debug info
                

                    duration_seconds = (end_datetime - start_datetime).total_seconds()
                    duration_minutes = int(duration_seconds // 60)
                    hours, minutes = divmod(duration_minutes, 60)
                    duration_formatted = f"{hours:02}:{minutes:02}"  # Format duration as HH:MM

                    day_formatted = day.strftime('%A %d-%m-%Y')

                    html += '''
                    <tr>
                        <td>{}</td>
                        <td>{}</td>
                        <td>{}</td>
                        <td>{}</td>
                    </tr>
                    '''.format(day_formatted, "WERK", event_time_formatted, duration_formatted)



                day += timedelta(days=1)


        # If no events were found, add a message to the HTML
        if not events_found:
            print("No schedule entries for this week")
            html += '''
                <tr>
                    <td colspan="4">No schedule entries for this week.</td>
                </tr>
            '''

        # Close the HTML table and body
        html += '''
            </table>
        </body>
        </html>
        '''

        # Debug
        # with open("test.html", 'w') as file:
        #     file.write(html)
        # print("HTML saved to test.html")

        
        return html