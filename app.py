from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

app = Flask(__name__)

def setup_driver():
    options = Options()
    options.add_argument("--headless")  # Run in headless mode for faster scraping
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    return driver

def get_price(driver):
    """Extracts the price using Amazon's updated selectors."""
    try:
        price_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "a-price-whole"))
        )
        price = price_element.text.strip()

        # Amazon sometimes stores decimal places separately
        fraction_element = driver.find_elements(By.CLASS_NAME, "a-price-fraction")
        if fraction_element:
            price += "." + fraction_element[0].text.strip()

        return price
    except:
        return "No Price Found"

def get_seller(driver):
    """Extracts the seller name using updated selectors."""
    try:
        seller_element = driver.find_element(By.ID, "sellerProfileTriggerId")
        return seller_element.text.strip()
    except:
        try:
            # Fallback: Check if the product is sold by Amazon
            seller_element = driver.find_element(By.CSS_SELECTOR, ".tabular-buybox-text-message")
            return seller_element.text.strip()
        except:
            return "No Seller Found"

@app.route('/scrape', methods=['POST'])
def scrape_amazon():
    data = request.json
    asins = data.get("asins", [])

    if not asins:
        return jsonify({"error": "No ASINs provided"}), 400

    driver = setup_driver()
    results = []

    try:
        for asin in asins:
            url = f"https://www.amazon.com/dp/{asin}?th=1&psc=1"
            driver.get(url)
            time.sleep(3)  # Allow time to load

            # Extract price and seller
            price = get_price(driver)
            seller = get_seller(driver)

            results.append({"asin": asin, "seller": seller, "price": price})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        driver.quit()

    return jsonify(results)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "ok", "message": "Amazon Scraper API is running. Use /scrape endpoint."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
