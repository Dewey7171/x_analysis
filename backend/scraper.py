from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_driver():
    """Chrome WebDriver 초기화"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def scrape_tweets(username, max_tweets=50):
    """트위터 크롤링 (비로그인 방식)"""
    logger.info(f"트위터 크롤링 시작: {username}")

    driver = init_driver()
    driver.get(f"https://x.com/{username}")
    time.sleep(3)

    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@data-testid='tweetText']")))
    except:
        logger.warning("트윗을 찾을 수 없음")
        driver.quit()
        return []

    tweets = set()
    retries = 0

    while len(tweets) < max_tweets and retries < 3:
        tweet_elements = driver.find_elements(By.XPATH, "//div[@data-testid='tweetText']")
        for tweet in tweet_elements:
            text = tweet.text.strip()
            if text:
                tweets.add(text)
            if len(tweets) >= max_tweets:
                break

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        retries += 1

    driver.quit()
    logger.info(f"크롤링 완료: {len(tweets)}개")
    return list(tweets)
