import yaml
from selenium import webdriver
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException

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


    def __init__(self) -> None:
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
    

    def get_table_list(self) -> list[dict[str, str]]:
        """
        Gets all the the tables from the blocks from the schedule with more info
        :return: A list of all block
        """

        # Get the current year and month
        current_date = datetime.now()
    
        # Calculate the start of the current week (Monday)
        current_week_start = current_date - timedelta(days=current_date.weekday())

        eight_weeks_ago_start = current_week_start - timedelta(weeks=8)

        four_weeks_later = current_week_start + timedelta(weeks=4)

        
        # Loop from the start of 8 weeks ago date to the last possible date
        date = eight_weeks_ago_start
        table_list = []
        print("Reading schedule...")
        while date < four_weeks_later:
            # Format the date as mm:dd:yyyy
            formatted_date = date.strftime('%m.%d.%Y')

            # Debug
            #print(f"Formatted date {formatted_date}")
            

            path = f"https://sam.ahold.com//etm/time/timesheet/etmTnsDetail.jsp?date={formatted_date}"
            self.driver.get(path)



            try:
                
                # Wait for the block info table to be present
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//table[@border='0'][4]//td"))
                )
                table_list.append(self.get_block_info())
            except NoSuchElementException as e:
                try:
                    no_data_message = self.driver.find_element(By.CSS_SELECTOR, 'span.datarowContent.etmWarning')
                    if 'Geen gegevens voor deze datum.' in no_data_message.text:
                        # Debug
                        print(f"Geen data voor datum: {formatted_date}, with message: {no_data_message.text}")
                        pass
                    else:
                        print(f"Found unkown no_data_message {no_data_message}")
                        raise e
                except NoSuchElementException as e:
                    print(f"Could not find no_data_mesage: {e}")
                    
            except TimeoutException:
                try:
                    system_error_message = self.driver.find_element(By.XPATH, "//*[contains(text(), 'System Error')]/following::td[1]")
                    print(f"Landed on system error page: {system_error_message}.")
                    pass
                except NoSuchElementException as e:
                    print(f"Could not find system_error_message: {e}")


                        
            # Move to the next day
            date += timedelta(days=1)


        self.driver.get(SCHEDULEPAGE)


        #Debug: print the entire table list
        #print("Starting table list:")
        #for index, block in enumerate(table_list):
        #    print(f"Block {index + 1}:")
        #    print(f"Day Html: {block['day_html']}")
        #    print(f"Table HTML: {block['table_html']}")
        #print("End of table list")

        return table_list

    def get_block_info(self) -> dict[str, str]:
        """
        Get the information from the current block, including the table HTML and the name of the current month.
        :returns: A dictionary containing the HTML of the table and the current month name.
        """
        
        # Define the XPath to match the correct table (assuming it's the fourth table with border 0)
        table_xpath = "//table[@border='0'][4]"
        month_xpath = "//span[@class='calMonthTitle']"  # XPath for the month name
        
        

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

        # Debug: Print the raw HTML of the table and month name
        #print("Raw HTML of the table:")
        #print(table_html)
        #print(f"Current Month Name: {day_html}")
        
        return {
            "table_html": table_html,
            "date_html": date_html
        }
    

    def get_year(self) -> str:
        """
        Gets the year the schedule is displaying.
        :return: The year. 
        """
        try:
            # Check if the current URL is valid for getting the year
            if self.driver.current_url not in [SCHEDULEPAGE, OTHERMONTHPAGE]:
                raise ValueError(
                    f"Can't get the year if we're not on the schedule page. Aborting...\n"
                    f"Current url: {self.driver.current_url}, Allowed urls: {SCHEDULEPAGE}, {OTHERMONTHPAGE}"
                )

            # Wait until the year title is present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'calYearTitle'))
            )

            # Find the element and get its innerHTML
            year_element = self.driver.find_element(By.CLASS_NAME, 'calYearTitle')
            return year_element.get_attribute('innerHTML')

        except ValueError as ve:
            print(ve)
            exit(1)
        except TimeoutException:
            print("Timeout while waiting for the year title element.")
            exit(1)
        except NoSuchElementException:
            print("Year title element not found.")
            exit(1)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            exit(1)


    def dispose(self) -> None:
        """
        Closes the browser window and ends the driver process.
        """
        self.driver.quit()


    
