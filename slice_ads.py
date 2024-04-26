import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    ElementNotInteractableException,
)
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import random
from urllib.request import Request, urlopen
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from utils import *

timeout = 60

url = "https://svnweb.freebsd.org/csrg/share/dict/words?revision=61569&view=co"
req = Request(url, headers={"User-Agent": "Mozilla/5.0"})

web_byte = urlopen(req).read()

webpage = web_byte.decode("utf-8")
WORDS = webpage.split("\n")

# https://github.com/reek/anti-adblock-killer
options = webdriver.ChromeOptions()
options.add_argument(
    "--user-data-dir=C:/Users/allan/AppData/Local/Google/Chrome/User Data/Profile 10"
)
# options.add_argument("--profile-directory=Profile 10")
# options.add_argument("--remote-debugging-port=9222")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-setuid-sandbox")
d = DesiredCapabilities.CHROME
d["goog:loggingPrefs"] = {"browser": "ALL"}
browser1 = webdriver.Chrome(
    executable_path=r"C:\Users\allan\chromdriver\chromedriver.exe",
    options=options,
    desired_capabilities=d,
)
browser1.set_page_load_timeout(timeout)
browser1.set_script_timeout(timeout)
actions = ActionChains(browser1)


def check_affiliate_limit(driver):
    for entry in driver.get_log("browser"):
        if "banner limit reached" in entry["message"]:
            print(entry["message"])
            time.sleep(60 * 60)
            return True
    return False


first_time = True


def check_captcha_exist(driver):
    current_url = driver.current_url
    if "google.com/sorry" in current_url:
        driver.delete_all_cookies()
        return True
    return False


def foo(driver: WebDriver, retry=0):
    global first_time
    random.shuffle(WORDS)
    get_with_retry(
        driver,
        f"https://www.google.com/search?q={WORDS[random.randint(0, len(WORDS))]}",
    )

    def execute():
        count = 0
        while True:
            status = check_captcha_exist(driver)
            if status:
                return foo(driver, retry)
            try:
                WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.ID, "pnnext"))
                )
                to_be_clicked = driver.find_element(By.ID, "pnnext")
                driver.execute_script("document.body.style.zoom='50%'")
                try:
                    for i in range(10):
                        driver.execute_script(f"window.scrollBy(0, {i * 100})")
                        time.sleep(1)
                    driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight)"
                    )
                    if count > 3:
                        break
                    driver.execute_script("arguments[0].click();", to_be_clicked)
                    should_reload = check_affiliate_limit(driver)
                    if should_reload:
                        return foo(driver, retry)
                    time.sleep(5)
                    count += 1
                except (
                    Exception,
                    StaleElementReferenceException,
                    ElementNotInteractableException,
                ) as e:
                    print(e)
                    if e.__class__.__name__ == "StaleElementReferenceException":
                        return foo(driver, retry)
            except Exception as e:
                print(e)
                time.sleep(120)
                return foo(driver)

    try:
        execute()
        foo(driver, retry)
    except Exception as e:
        print(e)
        foo(driver, retry)
    return


browser1.execute_script("window.open('');")
browser1.switch_to.window(browser1.window_handles[-1])
foo(browser1)
browser1.quit()
