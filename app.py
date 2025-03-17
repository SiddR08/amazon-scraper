from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--remote-debugging-port=9222")
    
    # Use ChromeDriverManager to handle driver installation
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

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
            url = f"https://www.amazon.com/dp/{asin}"
            driver.get(url)
            time.sleep(3)  # Give time to load

            soup = BeautifulSoup(driver.page_source, "html.parser")
            seller_element = soup.select_one("#sellerProfileTriggerId")
            price_element = soup.select_one(".a-price-whole")

            seller_name = seller_element.text.strip() if seller_element else "No Seller Found"
            price = price_element.text.strip() if price_element else "No Price Found"

            results.append({"asin": asin, "seller": seller_name, "price": price})

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