import requests
from bs4 import BeautifulSoup
import mysql.connector


def get_product_links_from_categories(category_url, main_url, num_pages):
    '''
    goes through each category and finds product_url to put into per product function
    :param category_url: eg. 'http://lazada.sg/shop-category/?page='
    :param num_pages: number of pages to go through per category
    '''
    for i in range(1,num_pages+1):
        soup = BeautifulSoup(requests.get(category_url+str(i)).text, "html.parser")
        for link in soup.findAll('a', {'class': 'c-product-card__name'}):
            href = main_url + link.get('href')
            product_info(href)
    return


def product_info(product_url):
    '''
    identifies various needed information per product to put into store_product function: [id, name, details, rating, store, price, discount, img_url, comments]
    :param product_url: url to product
    '''
    soup = BeautifulSoup(requests.get(product_url).text, "html.parser")
    print('from: ' + product_url)
    # Get product ID
    id = product_url.split('-')[-1][:-5]
    # Get product name
    name = soup.find('h1', {'id' : 'prod_title'}).string.strip()
    # Get product details
    details = ""
    for bullet in soup.find('ul', {'class': 'prd-attributesList ui-listBulleted js-short-description'}).findAll('span'):
        # if there is a string
        if bullet.string:
            details += "--" + bullet.string
    # Get product rating
    rating = soup.findAll('div', {'class': 'product-card__rating__stars '})
    if len(rating) != 0:
        rating = int(str(rating[0].findAll('div')[1].get('style')).split()[-1][:-1])
    else:
        rating = 0
    store = soup.findAll('a', {'class': 'product-fulfillment__item__link product__seller__name__anchor'})
    # when SOLD & FULFILLED BY Lazada no store link
    if len(store) == 0:
        store = 'Lazada'
    else:
        store = store[0].find('span').string.strip()
    # Get product price
    price = float(soup.find('span', {'id':'product_price'}).string)
    # Get product discount
    discount = soup.findAll('span', {'id': 'product_saving_percentage'})
    if len(discount) != 0:
        discount = float(discount[0].string[:-1])
    else:
        discount = 0
    # Get product image
    img_url = soup.findAll('img', {'class' : 'itm-img'})[-1].get('src')

    # Store data into the product table, returns True if successful
    store_product_info(soup, id, name, details, rating, store, price, discount, img_url)
    return


def store_product_info(soup, id, name, details, rating, store, price, discount, img_url):
    '''
    takes product info and stores into sql database 'ecommerce products'
    :param id: product id
    :param name: product name
    :param details: product details/description
    :param rating: product rating
    :param store: seller
    :param price: product final price
    :param discount: discount applied to original price
    :param img_url: url of one of product's images
    '''
    cnx = mysql.connector.connect(user='root', database='ecommerce_products', password="tiSPARTA3721")
    cursor = cnx.cursor()
    print("Storing the following data\n")
    details = cnx.converter.escape(details)
    store = cnx.converter.escape(store)
    img_url = cnx.converter.escape(img_url)
    print(id, name, details, rating, store, price, discount, img_url)
    add_product = ("INSERT IGNORE INTO product_description"
                   "(product_id, name, store, price, discount, details, picture, rating)"
                   "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")

    data_product = (id, name, store, price, discount, details, img_url, rating)
    print("Executing the query...\n")
    cursor.execute(add_product, data_product)
    if cursor.rowcount:
        # Get product comments and store them in comments table
        for review in soup.findAll('li', {'class' : 'ratRev_reviewListRow'}):
            review_rating = str(review.find('div', {'class':'product-card__rating__stars '}).findAll('div')[1].get('style')).split()[-1][:-1]
            review_title = cnx.converter.escape(review.find('span', {'class' : 'ratRev_revTitle'}).string.strip())
            review_details = cnx.converter.escape(str(review.find('div', {'class':'ratRev_revDetail'}).get_text()).strip())
            store_comment_info(id, review_rating, review_title, review_details)
    cnx.commit()
    cnx.close()
    cursor.close()
    return


def store_comment_info(id, review_rating, review_title, review_details):
    cnx = mysql.connector.connect(user='root', database='ecommerce_products', password="tiSPARTA3721")
    cursor = cnx.cursor()
    add_review = ("INSERT INTO comments"
                   "(product_id, comment_rating, title, details)"
                   "VALUES (%s, %s, %s, %s)")
    data_review = (id, review_rating, review_title, review_details)
    print("Storing the following comments\n")
    print(id, review_rating, review_title, review_details)
    cursor.execute(add_review, data_review)
    cnx.commit()
    cnx.close()
    cursor.close()
    return


if __name__ == "__main__":
    main_url = 'http://www.lazada.sg'
    categories = ['computers-laptops', 'cameras', 'consumer-electronics',
                  'womens-fashion', 'men-fashion',
                  'large-appliances', 'small-kitchen-appliances', 'kitchen-dining',
                  'furniture', 'home-decor', 'housekeeping', 'storage-organisation', 'home-improvement',
                  'health-beauty', 'toys-games', 'exercise-fitness']
    for category in categories:
        cat_url = main_url + '/shop-' + category + '/?page='
        get_product_links_from_categories(cat_url, main_url, 2)

# reasons for error: mysql.connector.errors.DatabaseError: 1366 (HY000): Incorrect string value: '\xE2\x9D\xA4'
#   other language, eg. chinese
#   emojis eg. ❤
#   unknown