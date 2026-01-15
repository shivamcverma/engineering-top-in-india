from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re, json, time
import os
from webdriver_manager.chrome import ChromeDriverManager
import platform

mba_sections = {
    "Top Engineering Colleges in India": "https://www.shiksha.com/engineering/ranking/top-engineering-colleges-in-india/44-2-0-0-0",
    # "Top Private Engineering Colleges in India":"https://www.shiksha.com/engineering/ranking/top-private-engineering-colleges-in-india/109-2-0-0-0",
    # "Top IITS in india":"https://www.shiksha.com/engineering/ranking/top-iits-colleges-in-india/113-2-0-0-0",
    # "Top  NITS in india":"https://www.shiksha.com/engineering/ranking/top-nits-colleges-in-india/115-2-0-0-0" ,
    # "Top Engineering Colleges in Banglore": "https://www.shiksha.com/engineering/ranking/top-engineering-colleges-in-bangalore/44-2-0-278-0",
    # "Top Engineering Colleges in karnataka":"https://www.shiksha.com/engineering/ranking/top-engineering-colleges-in-karnataka/44-2-106-0-0" ,
    # "Top Engineering Colleges in Hydrabaad":"https://www.shiksha.com/engineering/ranking/top-engineering-colleges-in-hyderabad/44-2-0-702-0",
    # "Top Engineering Colleges in Pune":"https://www.shiksha.com/engineering/ranking/top-engineering-colleges-in-pune/44-2-0-174-0" ,
    # "Top Engineering Colleges in Mumbai":"https://www.shiksha.com/engineering/ranking/top-engineering-colleges-in-mumbai/44-2-0-151-0",
    # "Top Engineering Colleges in Maharastra":"https://www.shiksha.com/engineering/ranking/top-engineering-colleges-in-maharashtra/44-2-114-0-0",
    # "Top Engineering Colleges in Chennai": "https://www.shiksha.com/engineering/ranking/top-engineering-colleges-in-chennai/44-2-0-64-0",
    # "Top Engineering Colleges in Kerla":"https://www.shiksha.com/engineering/ranking/top-engineering-colleges-in-kerala/44-2-107-0-0"  ,
    # "Top Engineering Colleges in Delhi":"https://www.shiksha.com/engineering/ranking/top-engineering-colleges-in-delhi/44-2-0-74-0"  ,
    # "Top Engineering Colleges in telangana":"https://www.shiksha.com/engineering/ranking/top-engineering-colleges-in-telangana/44-2-413-0-0",
    # "Top Engineering Colleges in gujarat":"https://www.shiksha.com/engineering/ranking/top-engineering-colleges-in-gujarat/44-2-109-0-0",
    # "Top Engineering Colleges in west-bengal":"https://www.shiksha.com/engineering/ranking/top-engineering-colleges-in-west-bengal/44-2-127-0-0",
}

def create_driver():
    options = Options()

    # Mandatory for GitHub Actions
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # Optional but good
    options.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    # Important for Ubuntu runner
    options.binary_location = "/usr/bin/chromium"

    service = Service(ChromeDriverManager().install())

    return webdriver.Chrome(
        service=service,
        options=options
    )

TEMP_FILE = "engineering_data.tmp.json"
FINAL_FILE = "engineering_data.json"

def scrape():
    driver = create_driver()
    all_sections_data = []
    c_count = 1

    try:
        for category_name, category_url in mba_sections.items():
            colleges_in_section = []

            for page in range(1, 9):
                url = category_url if page == 1 else f"{category_url}?pageNo={page}"
                driver.get(url)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(5)

                # Wait for cards to load
                WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "div.clear_float.desk-col.source-selected")
                    )
                )

                cards = driver.find_elements(By.CSS_SELECTOR, "div.clear_float.desk-col.source-selected")

                for card_element in cards:
                    try:
                        driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});", card_element
                        )
                        time.sleep(0.4)
                    
                        img_element = card_element.find_element(By.CSS_SELECTOR, "div.tuple-inst-img img")
                    
                        college_img = (
                            img_element.get_attribute("src")
                            or img_element.get_attribute("data-src")
                            or img_element.get_attribute("data-original")
                            or ""
                        )
                    except:
                        college_img = ""

 

                    try:
                        driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});", card_element
                        )
                        time.sleep(0.4)
                    
                        college_name = card_element.find_element(By.CSS_SELECTOR, "h4.f14_bold.link").text
                    except:
                        college_name = ""

                    try:
                        college_link = card_element.find_element(
                            By.CSS_SELECTOR, "div.tuple-inst-info a"
                        ).get_attribute("href")
                    except:
                        college_link = ""

                    try:
                        nirf_rank = card_element.find_element(By.CSS_SELECTOR, "div.flt_left.rank_section span.circleText").text
                    except:
                        nirf_rank = ""

                    fees, salary = "", ""
                    try:
                        for blk in card_element.find_elements(By.CSS_SELECTOR, "div.flex_v.text--secondary"):
                            text = blk.text
                            if "Fees" in text:
                                fees = text.replace("Fees", "").strip()
                            elif "Salary" in text:
                                salary = text.replace("Salary", "").strip()
                    except:
                        pass

                    business_today, outlook = "", ""
                    try:
                        for row in card_element.find_elements(By.CSS_SELECTOR, "div.rnkg_newsection"):
                            cols = row.find_elements(By.TAG_NAME, "div")
                            if len(cols) >= 2:
                                label = cols[1].text.lower()
                                match = re.search(r"\d+", cols[1].text)
                                number = match.group() if match else ""
                                if "business" in label:
                                    business_today = number
                                elif "outlook" in label:
                                    outlook = number
                    except:
                        pass

                    colleges_in_section.append({
                        "id":f"college_{c_count:03d}",
                        "college_img": college_img,
                        "name": college_name,
                        "nirf": nirf_rank,
                        "details": {
                            "fees": fees,
                            "salary": salary,
                            "rankings": {
                                "business_today": business_today,
                                "outlook": outlook
                            }
                        }
                    })
                    c_count += 1

                time.sleep(2)

            all_sections_data.append({
                "category": category_name,
                "colleges": colleges_in_section
            })

    finally:
        driver.quit()
    data = scrape()
    with open(TEMP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Atomic swap → replaces old file with new one safely
    os.replace(TEMP_FILE, FINAL_FILE)

    print("✅ Data scraped & saved successfully (atomic write)")

if __name__ == "__main__":
    scrape()
