import sys

sys.path.append("D:\presearch-bot")
import os
import base64
import io
import hashlib
import imagehash
from PIL import Image
from selenium import webdriver
from secrets import choice
import string
from selenium.webdriver.common.by import By
from utils import *
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

timeout = 60
folder = r"D:\presearch-bot\paidverts\images"
options = webdriver.ChromeOptions()
options.add_argument(
    "--user-data-dir=C:/Users/allan/AppData/Local/Google/Chrome/User Data/Profile 2"
)
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-setuid-sandbox")
browser = webdriver.Chrome(
    executable_path=r"C:\Users\allan\chromdriver\chromedriver.exe", options=options
)
browser.set_page_load_timeout(timeout)
browser.set_script_timeout(timeout)
image_hashes = {}


def generate_random_filename():
    filename = "".join(
        [choice(string.ascii_uppercase + string.digits) for _ in range(5)]
    )
    return filename


def download_image(decoded, image_hashes, image_hash):
    filename = generate_random_filename()
    img = Image.open(io.BytesIO(decoded))
    img.save(f"{folder}\{generate_random_filename()}.png", "PNG")
    print(f"downloaded as {filename}")
    image_hashes[image_hash] = filename


for filename in os.listdir(folder):
    with open(os.path.join(folder, filename), "rb") as f:
        src = f.read()
    image_hash = hashlib.sha256(src).hexdigest()
    image_hashes[image_hash] = filename

queries = {}
with open(os.path.join(folder, "queries.json"), "rb") as f:
    queries = json.load(f)
count = 0
first_time = True
while True:
    try:
        if first_time:
            get_with_retry(
                browser,
                "https://www.paidverts.com/login.html",
            )
            WebDriverWait(browser, timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "imgAnchor"))
            )
            first_time = False
        if count > 10:
            browser.refresh()
            count = 0
        images = browser.find_elements(By.CSS_SELECTOR, ".imgAnchor > img")
        query = browser.find_element(
            By.CSS_SELECTOR, ".visualCaptcha-explanation > strong"
        ).get_attribute("innerText")
        queries.update({query: 1})
        for img in images:
            src = img.get_attribute("src")
            if src:
                _, encoded = src.split(",", 1)
                decoded = base64.b64decode(encoded)
                image_hash = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
                if image_hash in image_hashes:
                    print(
                        f"{src} has already been downloaded as {image_hashes[image_hash]}"
                    )
                else:
                    image = Image.open(io.BytesIO(decoded))
                    phash = imagehash.phash(image)
                    if len(os.listdir(folder)) == 0:
                        download_image(decoded, image_hashes, image_hash)
                    else:
                        status = True
                        for filename in os.listdir(folder):
                            if filename == "queries.json":
                                continue
                            with open(os.path.join(folder, filename), "rb") as f:
                                existing_image = Image.open(io.BytesIO(f.read()))
                            existing_phash = imagehash.phash(existing_image)
                            if phash == existing_phash:
                                print(f"{src} is similar to {filename}")
                                status = False
                                break
                        if status:
                            download_image(decoded, image_hashes, image_hash)
        with open(os.path.join(folder, "queries.json"), "w") as f:
            json.dump(queries, f)

        to_be_clicked = browser.find_element(
            By.CLASS_NAME, "visualCaptcha-refresh-button"
        )
        to_be_clicked.click()
        time.sleep(3)
        count += 1
    except Exception as e:
        print(e)
        first_time = True
        time.sleep(60 * 20)
