import yaml
from selenium import webdriver
import locale
from datetime import datetime, timedelta
import calendar

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

LOGINPAGE = "https://sam.ahold.com/pingus_jct/idp/startSSO.ping?PartnerSpId=dingprod"
REDIRECTPAGE = "https://sam.ahold.com/wrkbrn_jct/etm/etmMenu.jsp?locale=nl_NL"
SCHEDULEPAGE = "https://sam.ahold.com/etm/time/timesheet/etmTnsMonth.jsp"
OTHERMONTHPAGE = "https://sam.ahold.com/wrkbrn_jct/etm/time/timesheet/etmTnsMonth.jsp"
class AlbertHeijn:
    def __login(self) -> None:
        """
        Logs the user in so he can access the schedule later on.
        :return: 
        """
        # Load the AH credentials.
        with open('settings.yaml') as s:
            settings = yaml.load(s, yaml.FullLoader)
        # Create a firefox driver.
        self.driver.get(LOGINPAGE)

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'uid'))
        ).send_keys(settings['username'])

        self.driver.find_element(By.ID, 'password').send_keys(settings['password'])
        # Log in.
        self.driver.find_element(By.CLASS_NAME, 'submitButton').click()


    def __load_schedule(self) -> None:
        """
        Loads the schedule
        """
        # Go to the main schedule page.
        self.driver.get(REDIRECTPAGE)
        # Click the 'Start' button.
        # Wait until the button is clickable
        WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "(//table[@class='imageButton'])[6]"))
        ).click()


    def __next_month_name_dutch(self) -> str:
        # Set locale to Dutch
        locale.setlocale(locale.LC_TIME, 'nl_NL.UTF-8')

        # Get the current date
        current_date = datetime.now()

        # Calculate the next month
        next_month = (current_date.month % 12) + 1
        next_year = current_date.year if next_month != 1 else current_date.year + 1

        # Create a date for the first day of the next month
        next_month_date = datetime(next_year, next_month, 1)

        # Get the month name in Dutch
        next_month_name = next_month_date.strftime('%B').capitalize()

        return next_month_name
    

    def __move_to_next_month(self) -> None:
        """
        Moves the webdriver to the next month
        """
        if self.driver.current_url != SCHEDULEPAGE and self.driver.current_url != OTHERMONTHPAGE:
            print("Can't get the  nextmonth if we're not on a month page. Aborting...")
            print(f"Current url: {self.driver.current_url}, Allowed urls: {SCHEDULEPAGE}, {OTHERMONTHPAGE}")
            exit(2)
        next_month_name = self.__next_month_name_dutch()
        
        # Click the button with the next month's name in Dutchelf.new_schedule_blocks()
        xpath = "(//table[@class='imageButton'])[9]"

        
        try:
            # Wait until the button is clickable
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            ).click()

            # Debug
            print(f"Clicked the '{next_month_name}' button successfully.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def __init__(self, mode: str = 'default') -> None:
        """
        Initializes a web client and logs the user in.
        """
        self.mode = mode
        if mode != 'default':
            print("Not running deafult mode")
            return
        with open('settings.yaml') as s:
            settings = yaml.load(s, yaml.FullLoader)


        # Setup Firefox options
        options = Options()
        if not settings.get('showbrowser', True):
            options.add_argument('--headless')

        # Assuming settings is a dictionary with 'geckopath' defined
        service = Service(executable_path=settings['geckopath'])
        
        print('Initializing web driver...')
        self.driver = webdriver.Firefox(service=service, options=options)

        print('Logging in...')
        self.__login()
        print('Loading the schedule...')
        self.__load_schedule()

    def get_schedule_blocks(self) -> list[str]:
        """
        Gets all the blocks from the schedule.
        :return: All blocks in a list.
        """
        # Fetch the elements for the current month
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//td[@height='62'][@valign='top']"))
        )

        all_elements_container = self.driver.find_elements(By.XPATH, "//td[@height='62'][@valign='top']")
        
        # Convert elements to outer HTML for the current month
        elements_html = [element.get_attribute('outerHTML') for element in all_elements_container]

        # Move to the next month
        self.__move_to_next_month()

        # Wait for elements in the next month to be present
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//td[@height='62'][@valign='top']"))
        )
        
        # Fetch the elements for the next month
        all_elements_container_next_month = self.driver.find_elements(By.XPATH, "//td[@height='62'][@valign='top']")
        # Convert elements to outer HTML for the next month
        elements_html += [element.get_attribute('outerHTML') for element in all_elements_container_next_month]
        
        return elements_html
    

    def get_table_list(self) -> list[dict[str, str]]:
        """
        Gets all the the tables from the blocks from the schedule with more info
        :return: A list of all block
        """

        # Get the current year and month
        current_date = datetime.now()
    
        # Calculate the start of the current week (Monday)
        current_week_start = current_date - timedelta(days=current_date.weekday())

        # Calculate the first Monday of the second week after the current one
        second_week_monday = current_week_start + timedelta(weeks=2)
        

        # Calculate the end of the week (Sunday)
        end_of_second_week = second_week_monday + timedelta(days=6)
        
        # Loop from the current date to the end of the current month
        
        table_list = []
        while current_date <= end_of_second_week:
            # Format the date as mm:dd:yyyy
            formatted_date = current_date.strftime('%m.%d.%Y')
            

            path = f"https://sam.ahold.com//etm/time/timesheet/etmTnsDetail.jsp?date={formatted_date}"
            self.driver.get(path)

            # Wait for the block info table to be present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//table[@border='0'][4]//td"))
            )

            try:
            # Check for the 'No data' message
                no_data_message = self.driver.find_element(By.CSS_SELECTOR, 'span.datarowContent.etmWarning')
                if 'Geen gegevens voor deze datum.' in no_data_message.text:
                    pass
            except NoSuchElementException:
                # We did not find the no data message, so there is data
                table_list.append(self.get_block_info())


            # Move to the next day
            current_date += timedelta(days=1)


        self.driver.get(SCHEDULEPAGE)


        # # Debug: print the entire table list
        # print("Starting table list:")
        # for index, block in enumerate(table_list):
        #     print(f"Block {index + 1}:")
        #     print(f"Day Html: {block['day_html']}")
        #     print(f"Table HTML: {block['table_html']}")
        # print("End of table list")

        return table_list

    def get_block_info(self) -> dict[str, str]:
        """
        Get the information from the current block, including the table HTML and the name of the current month.
        :returns: A dictionary containing the HTML of the table and the current month name.
        """
        
        # Define the XPath to match the correct table (assuming it's the fourth table with border 0)
        table_xpath = "//table[@border='0'][4]"
        month_xpath = "//span[@class='calMonthTitle']"  # XPath for the month name
        
        # Wait for the table to be present
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, table_xpath))
        )


        
        # Find the table element
        table_element = self.driver.find_element(By.XPATH, table_xpath)
        # Get the outer HTML of the table
        table_html = table_element.get_attribute('outerHTML')
        
        # Fetch the current month name
        try:
            date_element = self.driver.find_element(By.XPATH, month_xpath)
            date_html = date_element.get_attribute('innerHTML').strip()
        except Exception as e:
            print(f"Error retrieving the month name: {e}")
            date_html = "Unknown"

        # # Debug: Print the raw HTML of the table and month name
        # print("Raw HTML of the table:")
        # print(table_html)
        # print(f"Current Month Name: {day_html}")
        
        return {
            "table_html": table_html,
            "date_html": date_html
        }


    def get_month(self) -> str:
        """
        Gets the month the schedule is displaying.
        :return: The month. 
        """
        if self.driver.current_url != SCHEDULEPAGE and self.driver.current_url != OTHERMONTHPAGE:
            print("Can't get the month if we're not on the schedule page. Aborting...")
            print(f"Current url: {self.driver.current_url}, Allowed urls: {SCHEDULEPAGE}, {OTHERMONTHPAGE}")
            exit(2)


        # Wait until the month title is present
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'calMonthTitle'))
        )
        return self.driver.find_element(By.CLASS_NAME, 'calMonthTitle').get_attribute('innerHTML')

    def get_year(self) -> str:
        """
        Gets the year the schedule is displaying.
        :return: The year. 
        """
        if self.driver.current_url != SCHEDULEPAGE and self.driver.current_url != OTHERMONTHPAGE:
            print("Can't get the year if we're not on the schedule page. Aborting...")
            print(f"Current url: {self.driver.current_url}, Allowed urls: {SCHEDULEPAGE}, {OTHERMONTHPAGE}")

            exit(3)


        # Wait until the year title is present
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'calYearTitle'))
        )
        return self.driver.find_element(By.CLASS_NAME, 'calYearTitle').get_attribute('innerHTML')

    # TODO: Add something that gets the description from the shift, like TEAM, breaks and work description

    def dispose(self) -> None:
        """
        Closes the browser window and ends the driver process.
        """
        if self.mode != 'default':
            return
        self.driver.quit()


    
