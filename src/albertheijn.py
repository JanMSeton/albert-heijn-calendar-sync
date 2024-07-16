import time
import yaml
from selenium import webdriver


from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By



LOGINPAGE = "https://sam.ahold.com/pingus_jct/idp/startSSO.ping?PartnerSpId=dingprod"
REDIRECTPAGE = "https://sam.ahold.com/wrkbrn_jct/etm/etmMenu.jsp?locale=nl_NL"
SCHEDULEPAGE = "https://sam.ahold.com/etm/time/timesheet/etmTnsMonth.jsp"


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
        # Set the username and password.
        print(settings['username'])
        print(settings['password'])
        time.sleep(5)
        self.driver.find_element(By.ID, 'uid').send_keys(settings['username'])
        self.driver.find_element(By.ID, 'password').send_keys(settings['password'])
        # Log in.
        self.driver.find_element(By.CLASS_NAME, 'submitButton').click()

        time.sleep(1)

    def __load_schedule(self):
        """
        Loads the schedule and returns the content.
        :return: The work schedule in html.
        """
        # Go to the main schedule page.
        self.driver.get(REDIRECTPAGE)
        # Click the 'Start' button.
        self.driver.find_element(By.XPATH, "(//table[@class='imageButton'])[6]").click()
        time.sleep(1)

    def __init__(self):
        """
        Initializes a web client and logs the user in.
        """
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

    def get_blocks(self):
        """
        Gets all the blocks from the schedule.
        :return: All blocks in a list.
        """
        all_elements_container = self.driver.find_elements(By.XPATH, "//td[@height=\"62\"][@valign=\"top\"]")
        return [element.get_attribute('outerHTML') for element in all_elements_container]

    def get_month(self):
        """
        Gets the month the schedule is displaying.
        :return: The month. 
        """
        if self.driver.current_url != SCHEDULEPAGE:
            print("Can't get the month if we're not on the schedule page. Aborting...")
            exit(2)
        return self.driver.find_element(By.CLASS_NAME, 'calMonthTitle').get_attribute('innerHTML')

    def get_year(self):
        """
        Gets the year the schedule is displaying.
        :return: The year. 
        """
        if self.driver.current_url != SCHEDULEPAGE:
            print("Can't get the year if we're not on the schedule page. Aborting...")
            exit(3)
        return self.driver.find_element(By.CLASS_NAME, 'calYearTitle').get_attribute('innerHTML')

    def dispose(self):
        """
        Closes the browser window and ends the driver process.
        """
        self.driver.quit()


    
