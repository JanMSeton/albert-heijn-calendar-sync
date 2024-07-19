import time
import yaml
from selenium import webdriver
import locale
import datetime


from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

# Debug
from bs4 import BeautifulSoup



LOGINPAGE = "https://sam.ahold.com/pingus_jct/idp/startSSO.ping?PartnerSpId=dingprod"
REDIRECTPAGE = "https://sam.ahold.com/wrkbrn_jct/etm/etmMenu.jsp?locale=nl_NL"
SCHEDULEPAGE = "https://sam.ahold.com/etm/time/timesheet/etmTnsMonth.jsp"
OTHERMONTHPAGE = "https://sam.ahold.com/wrkbrn_jct/etm/time/timesheet/etmTnsMonth.jsp"
class AlbertHeijn:
    def __login(self):
        """
        Logs the user in so he can access the schedule later on.
        :return: 
        """
        # Load the AH credentials.
        with open('settings.yaml') as s:
            settings = yaml.load(s, yaml.FullLoader)
        # Create a firefox driver.
        self.driver.get(LOGINPAGE)

        time.sleep(6)
        self.driver.find_element(By.ID, 'uid').send_keys(settings['username'])
        self.driver.find_element(By.ID, 'password').send_keys(settings['password'])
        # Log in.
        self.driver.find_element(By.CLASS_NAME, 'submitButton').click()
        time.sleep(1)

    def __load_schedule(self):
        """
        Loads the schedule
        """
        # Go to the main schedule page.
        self.driver.get(REDIRECTPAGE)
        # Click the 'Start' button.
        self.driver.find_element(By.XPATH, "(//table[@class='imageButton'])[6]").click()

        time.sleep(1)


    def __next_month_name_dutch(self):
        # Set locale to Dutch
        locale.setlocale(locale.LC_TIME, 'nl_NL.UTF-8')

        # Get the current date
        current_date = datetime.datetime.now()

        # Calculate the next month
        next_month = (current_date.month % 12) + 1
        next_year = current_date.year if next_month != 1 else current_date.year + 1

        # Create a date for the first day of the next month
        next_month_date = datetime.datetime(next_year, next_month, 1)

        # Get the month name in Dutch
        next_month_name = next_month_date.strftime('%B').capitalize()

        return next_month_name
    

    def __move_to_next_month(self):
        """
        Moves the webdriver to the next month
        """
        next_month_name = self.__next_month_name_dutch()
        
        # Click the button with the next month's name in Dutch
        XPATH = "(//table[@class='imageButton'])[9]"

        
        try:
            self.driver.find_element(By.XPATH, XPATH).click()
            # Debug
            print(f"Clicked the '{next_month_name}' button successfully.")

            time.sleep(1)
        except Exception as e:
            print(f"An error occurred: {e}")

    def __init__(self, mode = 'default'):
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

    def get_schedule_blocks(self):
        """
        Gets all the blocks from the schedule.
        :return: All blocks in a list.
        """
        # Fetch the elements for the current month
        all_elements_container = self.driver.find_elements(By.XPATH, "//td[@height=\"62\"][@valign=\"top\"]")
        # Convert elements to outer HTML for the current month
        elements_html = [element.get_attribute('outerHTML') for element in all_elements_container]

        # Move to the next month
        self.__move_to_next_month()
        
        # Fetch the elements for the next month
        all_elements_container_next_month = self.driver.find_elements(By.XPATH, "//td[@height='62'][@valign='top']")
        # Convert elements to outer HTML for the next month
        elements_html += [element.get_attribute('outerHTML') for element in all_elements_container_next_month]
        
        return elements_html


    def get_month(self):
        """
        Gets the month the schedule is displaying.
        :return: The month. 
        """
        if self.driver.current_url != SCHEDULEPAGE and self.driver.current_url != OTHERMONTHPAGE:
            print("Can't get the month if we're not on the schedule page. Aborting...")
            print(f"Current url: {self.driver.current_url}, Allowed urls: {SCHEDULEPAGE}, {OTHERMONTHPAGE}")
            exit(2)
        return self.driver.find_element(By.CLASS_NAME, 'calMonthTitle').get_attribute('innerHTML')

    def get_year(self):
        """
        Gets the year the schedule is displaying.
        :return: The year. 
        """
        if self.driver.current_url != SCHEDULEPAGE and self.driver.current_url != OTHERMONTHPAGE:
            print("Can't get the year if we're not on the schedule page. Aborting...")
            print(f"Current url: {self.driver.current_url}, Allowed urls: {SCHEDULEPAGE}, {OTHERMONTHPAGE}")

            exit(3)
        return self.driver.find_element(By.CLASS_NAME, 'calYearTitle').get_attribute('innerHTML')

    # TODO: Add something that gets the description from the shift, like TEAM, breaks and work description

    def dispose(self):
        """
        Closes the browser window and ends the driver process.
        """
        if self.mode != 'default':
            return
        self.driver.quit()



    # Debug TODO: Fix this

    def _get_soup(self, filename):
        """
        Reads the HTML file and parses it with BeautifulSoup.
        :return: BeautifulSoup object containing the parsed HTML.
        """
        with open(filename, 'r', encoding='utf-8') as file:
            html_content = file.read()
        return BeautifulSoup(html_content, 'html.parser')

    def local_get_blocks(self, filename):
        """
        Gets all the blocks from an HTML file.
        :param filename: Name of the HTML file in the same directory.
        :return: All blocks in a list.
        """
        # Read the HTML file
        with open(filename, 'r', encoding='utf-8') as file:
            html_content = file.read()

        # Parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all elements matching the criteria
        all_elements = soup.find_all('td', attrs={'height': '62', 'valign': 'top'})

        # Return the outer HTML of each element
        return [str(element) for element in all_elements]

    def local_get_month(self, filename):
        """
        Gets the month the schedule is displaying from the HTML file.
        :return: The month as a string.
        """
        soup = self._get_soup(filename)
        month_element = soup.find(class_='calMonthTitle')
        if month_element:
            return month_element.get_text(strip=True)
        else:
            print("Month element not found. Aborting...")
            return None

    def local_get_year(self, filename):
        """
        Gets the year the schedule is displaying from the HTML file.
        :return: The year as a string.
        """
        soup = self._get_soup(filename)
        year_element = soup.find(class_='calYearTitle')
        if year_element:
            return year_element.get_text(strip=True)
        else:
            print("Year element not found. Aborting...")
            return None


    
