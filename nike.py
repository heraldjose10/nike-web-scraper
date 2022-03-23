import requests
import time
import pandas as pd
from pprint import pprint
from bs4 import BeautifulSoup


class NikeScrape():

    def __init__(self, browser, dbEngine) -> None:

        self.browser = browser
        self.dbEngine = dbEngine
        self.SCROLL_PAUSE_TIME = 2.5

        self.product_categories = []

        self.products = []

    def get_categories(self):
        """method to fetch categories from nike store"""
        url = 'https://www.nike.com/in/w/sale-3yaep'

        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')

        categories = soup.find_all('div', class_='categories')
        categories = categories[0].find_all('a')

        category_id = 1

        for category in categories:
            product_category = {
                'name': category.get_text(),
                '_link': category.get('href'),
                'id': category_id
            }
            self.product_categories.append(product_category)
            category_id += 1

    def get_products(self):
        """method to fetch products of each category"""
        for category in self.product_categories:
            self.browser.get(category['_link'])
            self.scroll()

            category_soup = BeautifulSoup(self.browser.page_source)
            products = category_soup.find_all('div', class_='product-card')
            p_count = 1

            for product in products:
                main_link = product.find_all(
                    'a', class_='product-card__link-overlay')
                name = product.find_all(
                    'div', class_='product-card__title')[0].get_text()
                price = product.find_all(
                    'div', class_='product-price is--current-price css-s56yt7')[0].get_text()
                short_description = product.find_all(
                    'div', class_='product-card__subtitle')[0].get_text()
                p = {
                    'product_category_id': category['id'],
                    'name': name,
                    '_link': main_link[0],
                    'id': p_count,
                    'price': price,
                    'short_description': short_description,
                    'long_description': None
                }
                self.products.append(p)
                p_count += 1

    def scroll(self):
        """function to scroll to end of the page"""

        last_height = self.browser.execute_script(
            "return document.body.scrollHeight")

        while True:
            # Scroll down to bottom
            self.browser.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            time.sleep(self.SCROLL_PAUSE_TIME)

            # Calculate new scroll height and compare with last scroll height
            new_height = self.browser.execute_script(
                "return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def print_data(self):
        pprint(self.product_categories)
        pprint(self.products)
        print(len(self.products))

    def save_to_db(self):
        df_product_categories = pd.DataFrame(self.product_categories)
        df_product_categories.drop('_link', 1, inplace=True)
        df_product_categories.to_sql(con=self.dbEngine, name='product_categories',
                                     if_exists='append', index=False)
