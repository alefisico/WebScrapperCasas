import sys
import argparse
import pandas as pd
from datetime import date
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def read_page_content(page, url):
    # Ensure mobile-friendly view for parsing
    useragent = "Mozilla/5.0 (Linux; Android 8.0.0; Pixel 2 XL Build/OPD1.170816.004) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Mobile Safari/537.36"

    #Firefox
    profile = webdriver.FirefoxProfile()
    profile.set_preference("general.useragent.override", useragent)
    options = webdriver.FirefoxOptions()
    options.set_preference("dom.webnotifications.serviceworker.enabled", False)
    options.set_preference("dom.webnotifications.enabled", False)
    options.add_argument('--headless')
    driver = webdriver.Firefox(executable_path='./geckodriver', firefox_profile=profile,options=options)
    driver.get(url%(page))
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "react-paging")))
    content = driver.page_source
    driver.quit()
    return content

def parse_item(item):
    price = item.find(attrs={'class': 'firstPrice'}).text.strip().replace('USD ', '')
    name = item.find(attrs={'class': 'postingCardTitle'}).a.text.strip()
    location = item.find(attrs={'class': 'postingCardLocation go-to-posting'}).span.text.strip()
    features = item.find(attrs={'class': 'postingCardMainFeatures go-to-posting'}).find_all("li")
    try: area = features[0].text.strip().replace("\t", "").replace("\n", "").split(' ')[0]
    except IndexError: area = 0
    try: bedrooms = features[1].text.strip().replace("\t", "").replace("\n", "").split(' ')[0]
    except IndexError: bedrooms = 0
    try: bathrooms = features[2].text.strip().replace("\t", "").replace("\n", "").split('ba')[0]
    except IndexError: bathrooms = 0
    try: garage = features[3].text.strip().replace("\t", "").replace("\n", "").split('es')[0]
    except IndexError: garage = 0

    return [name, location, price, area, bedrooms, bathrooms, garage]

def get_items_from_page(page_content):
    soup = BeautifulSoup(page_content, features="html.parser")
    page_items = []
    for item in soup.find_all(attrs={'class': 'postingCardInfo'}):
        page_items.append(parse_item(item))
    return page_items

def extract_items(filename, url):
    for i in range(1, args.numPages):
        print('extracting items from page %s'%(i))
        page_content = read_page_content(i, url)
        page_items = get_items_from_page(page_content)
        append_items_to_csv(page_items, filename)

def append_items_to_csv(items, filename):
    df = pd.DataFrame(items)
    df['date'] = date.today()
    df.to_csv(filename, index=False, header=False, mode='a')
    print('%s items appended to csv'%(df.shape[0]))

def create_csv_file_with_headers(name):
    today = date.today()
    output_filename = f'{name}_quito_{today}.csv'
    df = pd.DataFrame([["nombre", "sector", "precio", "area", 'habitaciones', 'banos', 'parqueadero', 'fecha']])
    df.to_csv(output_filename, index=False, header=False)
    return output_filename

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--inmueble', help='Tipo de inmueble: casa o departamento')
    parser.add_argument('--venta', action='store_true', help='Flag: venta')
    parser.add_argument('--numPages', type=int, default=100, help='Maximo numero de paginas scrapped')
    args = parser.parse_args()
    print(args)

    infoDict = {}
    if args.inmueble.startswith(('all', 'departamento')):
        if args.venta: infoDict[ 'departamentoVenta' ] = 'https://www.plusvalia.com/departamentos-en-venta-en-quito-pagina-%s.html'
        else: infoDict[ 'departamentoAlquiler' ] = 'https://www.plusvalia.com/departamentos-en-alquiler-en-quito-pagina-%s.html'
    if args.inmueble.startswith(('all', 'casa')):
        if args.venta: infoDict[ 'casasVenta' ] = 'https://www.plusvalia.com/casas-en-venta-en-quito-pagina-%s.html'
        else: infoDict[ 'casasAlquiler' ] = 'https://www.plusvalia.com/casas-en-alquiler-en-quito-pagina-%s.html'

    for name, url in infoDict.items():
        extract_items(create_csv_file_with_headers(name), url)
