import sqlalchemy
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

from nike import NikeScrape

load_dotenv()

# handle Firefox web driver installation
browser = webdriver.Firefox(service=Service(GeckoDriverManager().install()))

# DB_URI = os.getenv('DATABASE_URI')
DB_URI = 'sqlite:///nike.db'

dbEngine = sqlalchemy.create_engine(DB_URI)


if __name__ == '__main__':
    nike_scrape = NikeScrape(browser, dbEngine)
    nike_scrape.get_categories()
    nike_scrape.get_products()
    nike_scrape.get_product_styles()

    nike_scrape.save_to_db()

    # close Firefox web driver
    browser.close()