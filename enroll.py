from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
import logging
from selenium.webdriver.common.by import By
import argparse
from requests_html import HTML

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s.%(msecs)03d %(levelname)-6s %(name)s :: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

LOGIN_URL = "https://epprd.mcmaster.ca/psp/prepprd/?cmd=login"
ENROLL_URL = "https://csprd.mcmaster.ca/psc/prcsprd/EMPLOYEE/SA/c/SA_LEARNER_SERVICES.SSR_SSENRL_CART.GBL?" \
             "Page=SSR_SSENRL_CART&Action=A&ACAD_CAREER=UGRD&EMPLID={STUDENTNUM}&INSTITUTION=MCMST&STRM={TERMNUM}"

parser = argparse.ArgumentParser(description="Mosaic Auto Enroller")
parser.add_argument('-u', '--username', help='Mosaic Username', required=True)
parser.add_argument('-p', '--password', help='Mosaic Password', required=True)
parser.add_argument('-n', '--student_num', help="Student Number", required=True)
parser.add_argument('-c', '--course_id', help="Course ID", required=True)
parser.add_argument('-t', '--term', help="The term course is in", required=True)
args = parser.parse_args()
USERNAME = args.username
STUDENT_NUMBER = args.student_num
PASSWORD = args.password
TERM = args.term
COURSE_ID = args.course_id

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

def scraper(url):
    options = Options()
    # options.add_argument("--headless")
    driver.get(url)
    time.sleep(2)
    return driver.page_source


def login(url):
    logger.info("Logging in ...")
    driver.get(url)
    un_input = driver.find_element(By.NAME, 'userid')
    pw_input = driver.find_element(By.NAME, 'pwd')
    un_input.send_keys(USERNAME)
    time.sleep(1)
    pw_input.send_keys(PASSWORD)
    time.sleep(1)
    submit_btn = driver.find_element(By.NAME, 'Submit')
    submit_btn.click()
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//form[contains(@id,'PT_LANDINGPAGE')]")))
        logger.info("Log in succeed!")
    except Exception as e:
        logger.error("Log in failed " + str(e))
        driver.quit()


def add_to_cart(url, course_id, term):
    TERM_MAP = {
        "2022 Winter": 2221,
        "2022 Spring/Summer": 2225
    }

    # get term ID and complete enroll url
    term_num = TERM_MAP[term]
    enroll_url = url.format(TERMNUM=term_num, STUDENTNUM = STUDENT_NUMBER)
    driver.get(enroll_url)

    # search class
    class_input = driver.find_element(By.ID, "DERIVED_REGFRM1_CLASS_NBR")
    class_input.send_keys(course_id)
    time.sleep(1)

    search_btn = driver.find_element(By.ID, "DERIVED_REGFRM1_SSR_PB_ADDTOLIST2$9$")
    search_btn.click()
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@id='win0divDERIVED_CLS_DTL_DESCR50']")))
    logger.info("succeed getting to enroll page")

    # check if any labs or tutorials needs to be selected
    if EC.presence_of_element_located((By.XPATH, '//td[text()="Select Tutorial section (Required):" or text()="Select Laboratory section (Required):"]')):
        all_sections = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//tr[contains(@id, 'trSSR_CLS_TBL_R1')]")))
        for idx, section in enumerate(all_sections):
            try:
                section.find_element(By.XPATH, "//img[contains(@alt, 'Open')]")
                time.sleep(1)
                logger.info("Found available lab/tut section")
                select_btn = section.find_element(By.XPATH, "//input[contains(@title, 'Select this row')]")
                time.sleep(1)
                select_btn.click()
                time.sleep(1)
                break
            except Exception as e:
                if idx == len(all_sections):
                    logger.error("No available lab/tut section, quiting")
                    driver.quit()
                continue
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[contains(@title, 'Next Item')]"))).click()
        time.sleep(1)
        logger.info("Added lab/tut section")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//td[text()='Class Preferences']")))
    #Collecting table
    course_table = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//table[contains(@dir, 'ltr')]")))
    time.sleep(2)
    if course_table:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[contains(@title, 'Next Item')]"))).click()
        time.sleep(1)
        return course_table
    else:
        logger.error("Can't find the course table, bugging out...")
        driver.quit()


if __name__ == "__main__":
    # html_str = scraper(url)
    # content = HTML(html=html_str)
    # user_input = content.find(".userid", first=True)
    # pw_input = content.find(".pwd", first=True)

    login(LOGIN_URL)
    print(add_to_cart(ENROLL_URL, COURSE_ID, TERM))
