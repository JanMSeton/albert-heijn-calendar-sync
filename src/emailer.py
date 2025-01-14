from datetime import datetime, timedelta
import pytz
import yaml
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from typing import Iterator, Any, Optional


DUTCHMONTHS = [
    'januari', 'februari', 'maart', 'april', 'mei', 'juni',
    'juli', 'augustus', 'september', 'oktober', 'november', 'december'
]
class Email:

    def __init__(self)-> None:
        

        with open('settings.yaml') as s:
                settings = yaml.load(s, yaml.FullLoader)
        
        # Email credentials and SMTP server configuration
        self.from_email = str(settings['your_email'])
        self.to_email = str(settings['send_to_email'])
        self.password = str(settings['your_email_password'])
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.timezone = pytz.timezone(settings['timezone'])
        self.two_weeks_from_now = self.__get_week_start_and_end__(2)
        self.weeknumber = 0 # Needed in title of email


    def __get_week_start_and_end__(self, weeks_from_now: int) -> tuple[datetime, datetime]:
        """
        Calculate the start and end dates of the week `weeks_from_now` weeks from now.

        :param weeks_from_now: Number of weeks from now to calculate.
        :return: A tuple with start and end dates of the week.
        """
        # Get the current date
        today = datetime.now()
        
        # Calculate the start of the current week (Monday)
        start_of_week = today - timedelta(days=today.weekday())
        
        # Calculate the start of the target week
        start_of_target_week = start_of_week + timedelta(weeks=weeks_from_now)
        
        # Calculate the end of the target week (Sunday)
        end_of_target_week = start_of_target_week + timedelta(days=6)
        
        return self.timezone.localize(start_of_target_week), self.timezone.localize(end_of_target_week)
    
        


    def send_email(self, start_send_window: datetime, end_send_window: datetime, json: Iterator[dict[str, Any]]) -> None:



        if start_send_window.isocalendar()[1] == end_send_window.isocalendar()[1]:
            self.weeknumber = start_send_window.isocalendar()[1]
        else:
            self.weeknumber = f"{start_send_window.isocalendar()[1]} tot week {end_send_window.isocalendar()[1]}"
        subject = f"Rooster voor week {self.weeknumber}"

        body = self.__generate_schedule_table__(start_send_window, end_send_window, json)
        
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

    

    def send_changed_weeks_email(self, changed_events: list[dict[str, Any]], json: Iterator[dict[str, Any]]) -> None:
        weeks_set = set()

        for event in changed_events:
            event_datetime = datetime.fromisoformat(event['start']['dateTime']).astimezone(self.timezone)
            week_number = event_datetime.isocalendar()[1]
            year = event_datetime.isocalendar()[0]
            weeks_set.add((year, week_number))

        for year, week in sorted(weeks_set):
            # Calculate the first and last day of the week
            first_day_of_week = datetime.fromisocalendar(year, week, 1)
            last_day_of_week = first_day_of_week + timedelta(days=6)
            self.send_email(first_day_of_week, last_day_of_week, json)


        



    # Helper function to convert time string "H:M" to total minutes
    def __time_string_to_minutes__(self, time_str: str) -> int:
        if time_str:
            time_str = time_str.split('<')[0].strip()  # Remove HTML tags and extra characters            
            hours, minutes = map(int, time_str.split(':'))
            return hours * 60 + minutes
        return 0
    

    # Convert total break minutes to hours:minutes format
    def __minutes_to_time_string__(self, total_minutes: int) -> str:
        hours, minutes = divmod(total_minutes, 60)
        return f"{hours:02}:{minutes:02}"


    def __generate_schedule_table__(self, start_send_window: datetime, end_send_window: datetime, json: Iterator[dict[str, Any]]) -> Optional[str]:
        print("Generating schedule table...")

        # Debug
        #print("The first Monday of the second week after the current one is:", second_week_monday.strftime("%Y-%m-%d"))
        #print("The end of that week is:", end_of_week.strftime("%Y-%m-%d"))

        # Calculate dates of the current week
        # Calculate how many days to the next Monday


        # Flag to check if any event has been added
        events_found = False

        descriptions = [""] * 7 
        durations = [0] * 7 
        schedule = [[] for _ in range(7)]  # List of lists for multiple events per day
        unpaid_breaks = [0] * 7  # List to accumulate unpaid break minutes for each day
        paid_breaks = [0] * 7  # List to accumulate paid break minutes for each day
        total_worked_minutes = 0

        start_send_window= start_send_window.replace(hour=0, minute=0, second=0, microsecond=0)
        end_send_window = end_send_window.replace(hour=0, minute=0, second=0, microsecond=0)

        # Debug
        print(f"Start_send_window: {start_send_window}, end_send_window: {end_send_window}")


        # Add rows for all schedule entries matching the current day
        for event in json:
            # Debug
            #print(f"Looking at event: {event}")

            events_found = True

            start_datetime = datetime.fromisoformat(event['start']['dateTime']).astimezone(self.timezone)
            end_datetime = datetime.fromisoformat(event['end']['dateTime']).astimezone(self.timezone)

            # Send an email for the second week from now
            if(start_datetime < start_send_window):
                # Debug
                print(f"Skipped event:  The current event starts at {start_datetime}, which is before {start_send_window}")
                continue
            if(start_datetime > end_send_window):
                # Debug
                print(f"Processed all events: The current event starts at {start_datetime} which is after {end_send_window}")
                break
            print(f"Adding current event to schedule table which starts at {start_datetime}")

            # Debug
            #print(f"Event looks like: {event_time_str}")
        
            # Calculate the index for the day of the week
            day_of_week = (start_datetime.date() - end_send_window.date()).days

            if 0 <= day_of_week < 7:

                # Debug
                #print(f"Day of week: {day_week_of_week})
            
                duration_seconds = (end_datetime - start_datetime).total_seconds()
                duration_minutes = int(duration_seconds // 60)
                durations[day_of_week] += duration_minutes
                total_worked_minutes += duration_minutes

                # Convert escaped newlines to HTML line breaks and remove the signature
                description = event['description'].replace('\n', '<br>').replace('Event gemaakt door albert-heijn-calender-sync', '')

                # Extract the team name
                start_team_pos = description.find("Team:")
                start_team_pos += len("Team:")
                end_team_pos = description.find(",", start_team_pos)
                team = description[start_team_pos:end_team_pos].strip()

                # Extract break times
                start_unpaid_pos = description.find("Pauze (Onbetaald): ")
                start_paid_pos = description.find("Pauze (Betaald): ")

                if start_unpaid_pos != -1:
                    end_unpaid_pos = description.find(',', start_unpaid_pos)
                    if end_unpaid_pos == -1:
                        end_unpaid_pos = len(description)
                    unpaid_time_str = description[start_unpaid_pos + len("Pauze (Onbetaald): "):end_unpaid_pos].strip()
                    unpaid_breaks[day_of_week] += self.__time_string_to_minutes__(unpaid_time_str)

                if start_paid_pos != -1:
                    end_paid_pos = description.find(',', start_paid_pos)
                    if end_paid_pos == -1:
                        end_paid_pos = len(description)
                    paid_time_str = description[start_paid_pos + len("Pauze (Betaald): "):end_paid_pos].strip()
                    paid_breaks[day_of_week] += self.__time_string_to_minutes__(paid_time_str)

                schedule[day_of_week].append(f"{start_datetime.strftime('%H:%M')} - {end_datetime.strftime('%H:%M')} {team}")

                # Accumulate descriptions
                descriptions[day_of_week] += description[:start_unpaid_pos].replace(description[start_paid_pos:], "") + "<br>"

        for i in range(7):
            total_worked_minutes -= (unpaid_breaks[i] + paid_breaks[i])
            unpaid_breaks[i] = self.__minutes_to_time_string__(unpaid_breaks[i])
            paid_breaks[i] = self.__minutes_to_time_string__(paid_breaks[i])
            durations[i] = self.__minutes_to_time_string__(durations[i])


        # Generate the formatted dates for the week in one line
        dates = [
            f"{(start_send_window + timedelta(days=i)).day} " + 
            f"{DUTCHMONTHS[(start_send_window + timedelta(days=i)).month - 1]} " + 
            f"{ (start_send_window + timedelta(days=i)).year}"
            for i in range((end_send_window - start_send_window).days + 1)
        ]
        # Debug
        print(dates)


        return self.__generate_html__(dates, schedule, unpaid_breaks, paid_breaks, durations, descriptions, total_worked_minutes, events_found)


    def __generate_html__(self, dates: list[str], schedule: list[list[str]], unpaid_breaks: list[int], paid_breaks: list[int],
                           durations: list[int], descriptions: list[str], total_worked_minutes: int, events_found: bool):
        # Basic styles
        styles = """
        <style type="text/css">
        .body-text {
            font-family: Arial, sans-serif;
        }
        </style>
        """


        # Header
        html = f"""
        Hoi,
        <br><br>
        Je nieuwe rooster voor week {self.weeknumber} is:
        <br><br>
        <!--[if mso]>
        {styles}
        <![endif]-->
        <table id="week-schedule" style='width: 100%; min-width:800px;' cellspacing='0'>
            <thead>
            <tr>
                <td class="body-text" style="
                    width: 95px;
                    background: transparent;
                    border-bottom-width: 0px;
                    text-align: right;
                    border-right: 1px solid #dedede;
                    padding: 6px;
                    vertical-align: top;">
                </td>
        """
        
        # Days of the week headers
        days = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
        for day in days:
            html += f"""
                <td class="body-text" style="
                    border-right: 1px solid #dedede;
                    padding: 6px;
                    width: 118px;
                    vertical-align: top;">
                    {day}
                </td>
            """
        
        html += """
        </tr>
            <tr>
                <td class="body-text" style="
                    width: 95px;
                    background: transparent;
                    border-bottom-width: 0px;
                    text-align: right;
                    border-right: 1px solid #dedede;
                    padding: 6px;
                    vertical-align: top;">
                </td>"""
        
        # Dates
        for date in dates:
            html += f"""
                <td class="body-text" style="
                    border-right: 1px solid #dedede;
                    width: 118px;
                    vertical-align: top;
                    background: #f0f0f0;
                    padding: 3px 6px;">
                    {date}
                </td>
            """
        
        html += "</tr>\n</thead>\n<tbody>\n"
        
        # Schedule
        html += "<tr>\n"
        html += f"""
            <td class="body-text" style="
                width: 95px;
                background: transparent;
                border-bottom-width: 0px;
                text-align: right;
                border-right: 1px solid #dedede;
                padding: 6px;
                vertical-align: top;">
            </td>
        """
        for events in schedule:
            if events:
                html += f"""
                    <td class="body-text" style="
                            border-right: 1px solid #dedede;
                            width: 118px;
                            vertical-align: top;
                            padding: 6px;
                            border-bottom: 1px solid #dedede;">
                            """
                for event in events:
                    html += f"""
                            <div style="background-color: #ebffe4; border-top: 1px solid #fff; padding: 3px 6px;">
                                {event}
                            </div>
                        """
                    
                html += f"""
                    </td>
                            """
            else:
                html += """
                    <td class="body-text" style="
                        border-right: 1px solid #dedede;
                        width: 118px;
                        vertical-align: top;
                        padding: 6px;
                        border-bottom: 1px solid #dedede;">
                    </td>
                """
        html += "</tr>\n"
        
        # Footer (with example rows for "Pauze", "Productieve uren", etc.)
        footer_rows = [
            ("Pauze Onbetaald", unpaid_breaks),
            ("Pauze Betaald", paid_breaks),
            ("Productieve uren", durations),
            ("Toeslagen", [""] * 7), # TODO: Maybe add toeslagen
            ("Opmerkingen", descriptions) 
            # TODO: maybe add verlof here
        ]
        
        html += "<tfoot>\n"
        for label, values in footer_rows:
            html += "<tr>\n"
            html += f"""
                <td class="body-text" style="
                    width: 95px;
                    background: transparent;
                    border-bottom-width: 0px;
                    text-align: right;
                    border-right: 1px solid #dedede;
                    padding: 6px;
                    vertical-align: top;">
                    {label}
                </td>
            """
            for value in values:
                html += f"""
                    <td class="body-text" style="
                        border-right: 1px solid #dedede;
                        width: 118px;
                        vertical-align: top;
                        padding: 6px;
                        border-bottom: 1px solid #dedede;">
                        {value}
                    </td>
                """
            html += "</tr>\n"
        
        html += "</tfoot>\n</table>\n<br/><br/>\n"

        html += f"""
                <div class=3D"body-text" style=3D"margin: 15px 0 0 100px; font-family: =
Arial, sans-serif;">
        Totaal week: {self.__minutes_to_time_string__(total_worked_minutes)}    </div>
        """
    

        # If no events were found, add a message to the HTML
        if not events_found:
            print("No schedule entries for this week")
            html += '''
                <tr>
                    <td colspan="4">No schedule entries for this week.</td>
                </tr>
            '''

        # Debug
        #with open("test.html", 'w') as file:
        #     file.write(html)
        #print("HTML saved to test.html")


        return html