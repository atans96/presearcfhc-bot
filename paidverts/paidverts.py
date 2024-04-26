import sys

sys.path.append("D:\presearch-bot")
import os
from skimage.metrics import structural_similarity as ssim
from imageio import imread
from PIL import Image
import numpy as np
import io
from selenium import webdriver
from secrets import choice
import string
from selenium.webdriver.common.by import By
from utils import *
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import base64
import cv2

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


def generate_random_filename():
    filename = "".join(
        [choice(string.ascii_uppercase + string.digits) for _ in range(5)]
    )
    return filename


def mse(imageA, imageB):
    err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
    err /= float(imageA.shape[0] * imageA.shape[1])
    return err


def solve_captcha():
    try:
        WebDriverWait(browser, timeout).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".visualCaptcha-explanation > strong")
            )
        )
        query = (
            browser.find_element(By.CSS_SELECTOR, ".visualCaptcha-explanation > strong")
            .get_attribute("innerText")
            .lower()
        )
        images = browser.find_elements(By.CSS_SELECTOR, ".imgAnchor > img")
        for img in images:
            src = img.get_attribute("src")
            index = img.get_attribute("data-index")
            if index == "4":
                to_be_clicked = browser.find_element(
                    By.CLASS_NAME, "visualCaptcha-refresh-button"
                )
                try:
                    to_be_clicked.click()
                except Exception as e:
                    print(e)
                    return False
                time.sleep(3)
                return solve_captcha()
            if src:
                _, encoded = src.split(",", 1)
                decoded = base64.b64decode(encoded)
                decoded = imread(io.BytesIO(decoded))
                cv2_img_url = cv2.cvtColor(decoded, cv2.COLOR_RGB2BGR)
                with open(os.path.join(folder, f"{query.title()}.png"), "rb") as f:
                    existing_image = imread(io.BytesIO(f.read()))
                existing_image = cv2.cvtColor(existing_image, cv2.COLOR_RGB2BGR)
                mse_score = mse(cv2_img_url, existing_image)
                ssim_score = ssim(cv2_img_url, existing_image, multichannel=True)
                print(f"mse: {mse_score} ssim: {ssim_score}")
                if mse_score < 500 and ssim_score > 0.9:
                    try:
                        img.click()
                    except Exception as e:
                        print(e)
                        return False
                    return True
        return False
    except Exception as e:
        print(e)
        return 1


def go_through_ads(browser):
    status_after_captcha = solve_captcha()
    if type(status_after_captcha) == int:
        return 1
    if not status_after_captcha:
        browser.refresh()
        return go_through_ads(browser)
    to_be_clicked = browser.find_element(By.CLASS_NAME, "button_captcha")
    try:
        to_be_clicked.click()
    except Exception as e:
        return False
    try:
        WebDriverWait(browser, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "is-countdown"))
        )
    except Exception as e:
        print(e)
        time.sleep(5)
        return go_through_ads(browser)
    while True:
        countdown = (
            browser.find_element(By.CLASS_NAME, "is-countdown")
            .get_attribute("innerText")
            .lower()
        )
        if countdown == "0 seconds":
            to_be_clicked = browser.find_element(By.ID, "nextAdBtn")
            try:
                to_be_clicked.click()
            except Exception as e:
                print(e)
                return False
            break
        time.sleep(2)
    return True


while True:
    try:
        get_with_retry(
            browser,
            "https://www.paidverts.com/member/paid_ads.html",
        )
        WebDriverWait(browser, timeout).until(
            EC.presence_of_element_located((By.ID, "activationAds"))
        )
        ads = browser.find_elements(By.CSS_SELECTOR, ".activationAd a")
        for ad in ads:
            link = ad.get_attribute("href")
            if link:
                browser.execute_script("window.open('');")
                browser.switch_to.window(browser.window_handles[-1])
                get_with_retry(
                    browser,
                    link,
                )
                status = True
                while status:
                    status = go_through_ads(browser)
                    if type(status) == int:
                        browser.switch_to.window(browser.window_handles[-1])
                        browser.close()
                        break
                    current_url = browser.current_url
                    if "https://www.paidverts.com/member/paid_ads.html" in current_url:
                        break
    except Exception as e:
        print(e)
        time.sleep(60 * 20)
