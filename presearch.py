import time
import random
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib3.exceptions import MaxRetryError, NewConnectionError
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from tqdm import tqdm

timeout = 60
num_timeouts = 0
MAX_TIMEOUTS = 3


def get_with_retry(driver, url):
    global num_timeouts

    if num_timeouts >= MAX_TIMEOUTS:
        return print(url, "Gave up after earlier timeout")

    try:
        driver.get(url)

    except TimeoutException as e:
        num_timeouts += 1
        return print(url, "TimeoutException")

    except (ConnectionRefusedError, MaxRetryError, NewConnectionError) as e:
        # MaxRetryError and NewConnectionError come from urllib3.exceptions
        # ConnectionRefusedError is a Python builtin.
        num_timeouts += 1
        print("EEK! Connection error", e)
    except Exception as e:
        num_timeouts += 1
        print("EEK! Unexpected exception in driver.get: " + str(e))

    try:
        fullhtml = driver.page_source

    except Exception as e:
        num_timeouts += 1
        print("EEK! Fetched page but couldn't get html: " + str(e))


options = webdriver.FirefoxOptions()
options.add_argument("--width=800")

options.add_argument("--height=640")

profile = webdriver.FirefoxProfile(
    "C:/Users/allan/AppData/Roaming/Mozilla/Firefox/Profiles/ncjbo06z.default-release"
)

options.binary_location = "C:/Program Files/Mozilla Firefox/firefox.exe"
browser1 = webdriver.Firefox(firefox_profile=profile, options=options)
browser2 = webdriver.Firefox(firefox_profile=profile, options=options)
browser1.set_page_load_timeout(timeout)
browser1.set_script_timeout(timeout)
browser2.set_page_load_timeout(timeout)
browser2.set_script_timeout(timeout)


def foo(driver: WebDriver, text, retry=0):
    if retry > MAX_TIMEOUTS:
        return
    get_with_retry(driver, "https://www.presearch.org/?utm_source=extcr")
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'form[action="/search"]'))
        )
    except:
        print("Timed out waiting for search element to load. Retrying...")
        return foo(driver, text, retry + 1)
    try:
        print("Searching... " + text)
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="text"]'))
        )
        element.send_keys(text, Keys.ENTER)
        time.sleep(5)
    except:
        print("Timed out waiting for input element to load. Retrying...")
        return foo(driver, text, retry + 1)
    url = driver.current_url + f"&page={random.randint(1, 10)}"
    get_with_retry(driver, url)
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[contains(@id, "user-info")]')
            )
        )
    except:
        print("Timed out waiting for user-info XPATH to load. Retrying...")
        return foo(driver, text, retry + 1)
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'a span[x-html="result.title"]')
            )
        )
    except:
        print("Timed out waiting for result.title to load. Retrying...")
        return foo(driver, text, retry + 1)
    results = []
    try:
        elements = driver.find_elements(
            By.CSS_SELECTOR, 'a span[x-html="result.title"]'
        )
        links = [
            element.find_element(By.XPATH, ".//ancestor::a").get_attribute("href")
            for element in elements
        ]
        results.extend(links)
        if len(results) == 0:
            print("No results found.")
            return
    except:
        print("Timed out waiting for ancestor to load. Retrying...")
        return foo(driver, text, retry + 1)
    link = random.choice(results)
    try:
        driver.find_element(By.XPATH, "//a[starts-with(@href,'" + link + "')]").click()
    except:
        print("Timed out waiting for ancestor to load. Retrying...")
        return foo(driver, text, retry + 1)
    time.sleep(10)
    return


with open("search.txt", encoding="utf-8") as f:
    lines = f.read().splitlines()
    for i in tqdm(range(0, len(lines), 2)):
        text1 = lines[i]
        text2 = lines[i + 1] if i + 1 < len(lines) else None
        thread1 = threading.Thread(target=foo, args=(browser1, text1))
        thread1.start()
        if text2 is not None:
            thread2 = threading.Thread(target=foo, args=(browser2, text2))
            thread2.start()
            thread1.join()
            thread2.join()
        else:
            thread1.join()

# close the browser instances
browser1.quit()
browser2.quit()
