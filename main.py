import requests
from bs4 import BeautifulSoup
import numpy
import pandas as pd

def get_product_links_from_categories(category_url, main_url, num_pages, products):
    '''
    goes through each category and finds product_url to put into per product function
    :param category_url: eg. 'http://lazada.sg/shop-category/?page='
    :param num_pages: number of pages to go through per category
    '''
    for i in range(1,num_pages+1):
        soup = BeautifulSoup(requests.get(category_url+str(i)).text, "html.parser")
        for link in soup.findAll('a', {'class': 'c-product-card__name'}):
            href = main_url + link.get('href')
            products = products.append(product_info(href))
    print products.info()
    return products


def product_info(product_url):
    '''
    identifies various needed information per product to put into store_product function: [id, name, details, rating, store, price, discount, img_url, comments]
    :param product_url: url to product
    '''
    soup = BeautifulSoup(requests.get(product_url).text, "html.parser")
    print('from: ' + product_url)
    # Get product ID
    id = product_url.split('-')[-1].split('.')[0]
    # Get product name
    name = soup.find('h1', {'id': 'prod_title'}).string.strip()
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
    price = float(soup.find('span', {'id': 'product_price'}).string)
    # Get product discount
    discount = soup.findAll('span', {'id': 'product_saving_percentage'})
    if len(discount) != 0:
        discount = float(discount[0].string[:-1])
    else:
        discount = 0
    # Get product image
    img_url = soup.findAll('img', {'class' : 'itm-img'})[-1].get('src')

    # Store data into the product table, returns True if successful
    return store_product_info(id, name, details, rating, store, price, discount, img_url)


def store_product_info(id, name, details, rating, store, price, discount, img_url):
    '''
    takes product info and stores into csv file
    :param id: product id
    :param name: product name
    :param details: product details/description
    :param rating: product rating
    :param store: seller
    :param price: product final price
    :param discount: discount applied to original price
    :param img_url: url of one of product's images
    '''
    print "Storing the relevant data\n"
    return pd.DataFrame(data={'id': id, 'name': name, 'details': details, 'rating': rating, 'store': store, 'price': price, 'discount': discount, 'img_url': img_url}, index=[0])

if __name__ == "__main__":
    main_url = 'http://www.lazada.sg'
    categories = ['computers-laptops']
    products = pd.DataFrame(data={},
                            columns=['id', 'name', 'details', 'rating', 'store', 'price', 'discount', 'img_url'])
    # categories = ['computers-laptops', 'cameras', 'consumer-electronics',
    #               'womens-fashion', 'men-fashion',
    #               'large-appliances', 'small-kitchen-appliances', 'kitchen-dining',
    #               'furniture', 'home-decor', 'housekeeping', 'storage-organisation', 'home-improvement',
    #               'health-beauty', 'toys-games', 'exercise-fitness']
    for category in categories:
        cat_url = main_url + '/shop-' + category + '/?page='
        products = products.append(get_product_links_from_categories(cat_url, main_url, 1, products))
    products.to_csv('products.csv')

# reasons for error: mysql.connector.errors.DatabaseError: 1366 (HY000): Incorrect string value: '\xE2\x9D\xA4'
#   other language, eg. chinese
#   emojis eg.
#   unknown