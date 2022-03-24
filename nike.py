import requests
import time
import pandas as pd
from pprint import pprint
from bs4 import BeautifulSoup


class NikeScrape():

    def __init__(self, browser, dbEngine) -> None:

        self.browser = browser
        self.dbEngine = dbEngine

        self.SCROLL_PAUSE_TIME = 5

        self.product_categories = []
        self.products = []
        self.product_styles = []
        self.product_images = []

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
            print(f'---{product_category["id"]} {product_category["name"]}---')
            category_id += 1

    def get_products(self):
        """method to fetch products of each category"""
        p_count = 1

        for category in self.product_categories:
            self.browser.get(category['_link'])
            self.scroll()

            category_soup = BeautifulSoup(self.browser.page_source)
            products = category_soup.find_all('div', class_='product-card')

            for product in products:
                main_link = product.find_all(
                    'a', class_='product-card__link-overlay')
                name = product.find_all(
                    'div', class_='product-card__title')[0].get_text()
                price = product.find_all(
                    'div', class_='product-price is--current-price css-s56yt7')[0].get_text()
                price_in_number = price[1:].split(',')
                short_description = product.find_all(
                    'div', class_='product-card__subtitle')[0].get_text()
                p = {
                    'product_category_id': category['id'],
                    'name': name,
                    '_link': main_link[0].get('href'),
                    'id': p_count,
                    'price': int(''.join(price_in_number)),
                    'short_description': short_description,
                    'long_description': None
                }
                self.products.append(p)
                print(f'---{p["id"]} {p["name"]}---')
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

    def get_product_styles(self):
        """method to fetch product styles of each products"""
        product_style_id = 1

        self.product_image_id = 1

        for product in self.products:
            # open the page of the product
            self.browser.get(product['_link'])

            product_soup = BeautifulSoup(self.browser.page_source)
            product_description = product_soup.find_all('div', class_='description-preview')
            if product_description:
                long_description = product_description[0].find_all('p')[0].get_text()
                product['long_description'] = long_description

            styles_container = product_soup.find_all('div', class_='colorway-images')
            if styles_container:
                styles = styles_container[0]
                styles = styles.find_all('a')

                for style in styles:
                    # open different styles
                    self.browser.get(style.get('href'))
                    self.scroll()

                    style_soup = BeautifulSoup(self.browser.page_source)
                    color = style_soup.find_all(
                        'li', class_='description-preview__color-description')[0].get_text()
                    color_processed = color.split(':')[1][1:]
                    style = style_soup.find_all(
                        'li', class_='description-preview__style-color')[0].get_text()
                    style_processed = style.split(':')[1][1:]
                    ps = {
                        'id': product_style_id,
                        'product_id': product['id'],
                        'colour': color_processed,
                        'style_name': style_processed
                    }
                    self.product_styles.append(ps)
                    print(f'---{ps["id"]} {ps["colour"]} {ps["style_name"]}---')

                    self.get_product_images(style_soup, product_style_id)

                    product_style_id += 1

    def get_product_images(self, style_soup, product_style_id):
        """method to fetch images of different styles"""
        product_images = style_soup.find_all('div', class_='css-du206p')

        for image in product_images:
            picture_tag = image.find_all('picture')[1]
            img_tag = picture_tag.find_all('img')[0]
            # print(img_tag)
            if img_tag.has_attr('src'):
                img_url = img_tag['src']
                product_image = {
                    'id': self.product_image_id,
                    'product_style_id': product_style_id,
                    'image_url': img_url
                }
                self.product_images.append(product_image)
                print(f'---{product_image["id"]} {product_image["image_url"]}---')
                self.product_image_id += 1

    def save_to_db(self):
        df_product_categories = pd.DataFrame(self.product_categories)
        df_product_categories.drop('_link', 1, inplace=True)
        df_product_categories.to_sql(con=self.dbEngine, name='product_categories',
                                     if_exists='append', index=False)

        df_products = pd.DataFrame(self.products)
        df_products.drop('_link', 1, inplace=True)
        df_products.to_sql(con=self.dbEngine, name='products',
                           if_exists='append', index=False)

        df_product_styles = pd.DataFrame(self.product_styles)
        df_product_styles.to_sql(con=self.dbEngine, name='product_styles',
                                 if_exists='append', index=False)

        df_product_images = pd.DataFrame(self.product_images)
        df_product_images.to_sql(con=self.dbEngine, name='product_images',
                                 if_exists='append', index=False)