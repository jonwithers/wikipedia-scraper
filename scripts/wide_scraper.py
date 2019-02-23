from __future__ import print_function
from builtins import input
import pandas as pd
import requests
import os
from bs4 import BeautifulSoup
from googletrans import Translator
import datetime as dt
from time import sleep

today = dt.datetime.now()
today_string = dt.date.isoformat(today)[2:]
print(today_string)
print(os.path.isfile('../data/{}.csv'.format(today_string)))
if os.path.isfile('../data/{}.csv'.format(today_string))==False:
    pd.DataFrame(columns=['lang','text']).to_csv('../data/{}.csv'.format(today_string))

STARTING_MESSAGE = """
WELCOME TO THE WIKIPEDIA SCRAPER!
"""
def get_soup(url):
    results = requests.get(url)
    if results.status_code != 200:
        print("error", results.status_code)
    soup = BeautifulSoup(results.text, 'lxml')
    print(soup.text[:100])
    return soup

def get_zh_url_from_en_page(soup):
    if soup is None:
        print("error no soup")
        return None
    try:
        chinese_url = soup.find('a', {'class':'interlanguage-link-target', 'hreflang':'zh'})['href']
    except:
        return None
    if chinese_url is None:
        print("error No chinese link")
        return None
    return chinese_url

def get_page_text(soup, top=True, n_top=50):
    all_ps = soup.find('div',{'id':'mw-content-text'}).find_all('p')
    all_p_text = [i.text for i in all_ps]
    if top:
        text_list = sorted(all_p_text, key=len, reverse=True)[:n_top]
    else:
        text_list = [i for i in all_p_text if len(i) > 1000]
    return text_list


def add_text_to_file(text_list, dataset_label, filename):
    for i, text in enumerate(text_list):
        this_csv_row = pd.DataFrame({'lang':dataset_label, 'text':text}, index=[i])
        this_csv_row.to_csv(filename, mode='a', header=False, encoding='utf-8')

def translate_zh_to_en(text_list):
    translated=[]
    translator=Translator()
    for text in text_list:
        translated.append(translator.translate(text, src='zh-CN').text)
        sleep(2)
    return translated

def check_for_file(filename):
    if not os.path.isfile(filename):
        pd.DataFrame(columns=['lang','text']).to_csv(filename)

# def scrape_a_page(en_url, filename):
#     check_for_file(filename)
#     en_soup = get_soup(starting_url)
#     zh_soup = get_soup(get_zh_url_from_en_page(en_soup))
#     en_text = get_page_text(en_soup)
#     zh_text = get_page_text(zh_soup)
#     translated_zh_text = translate_zh_to_en(zh_text)
#     add_text_to_file(en_text, 'en', filename)
#     add_text_to_file(translated_zh_text, 'zh', filename)
#     df = pd.read_csv(filename, index_col=0).reset_index(drop=True)
#     print "added {} lines to {}".format(df.shape[0], filename)

def get_list_of_pages(soup):
    big_list = [i.find_all('a') for i in soup.find('div',{'id':'mw-content-text'}).find_all('p')]
    all_links = [item['href'] for sublist in big_list for item in sublist]
    return [i for i in all_links if i[:5]=='/wiki']

def wide_scrape(starting_url, filename):
    print(STARTING_MESSAGE)
    soup = get_soup(starting_url)
    l_of_ps = get_list_of_pages(soup)
    n_links = eval(input("There are {} links on this page. How many should I scrape? ".format(len(l_of_ps))))
    l_of_ps = l_of_ps[:n_links]
    check_for_file(filename)
    en_soup = get_soup(starting_url)
    zh_url = get_zh_url_from_en_page(en_soup)
    zh_soup = get_soup(zh_url)
    en_text = get_page_text(en_soup)
    zh_text = get_page_text(zh_soup)
    translated_zh_text = translate_zh_to_en(zh_text)
    add_text_to_file(en_text, 'en', filename)
    add_text_to_file(translated_zh_text, 'zh', filename)
    df = pd.read_csv(filename, index_col=0).reset_index(drop=True)
    print("added {} lines to {}".format(df.shape[0], filename))
    for link in l_of_ps:
        result = requests.get('https://en.wikipedia.org/'+link)
        en_soup = BeautifulSoup(result.text, 'lxml')
        zh_url = get_zh_url_from_en_page(en_soup)
        if zh_url is None:
            print("no chinese url")
            continue
        zh_soup = get_soup(zh_url)
        en_text = get_page_text(en_soup)
        zh_text = get_page_text(zh_soup)
        translated_zh_text = translate_zh_to_en(zh_text)
        add_text_to_file(en_text, 'en', filename)
        add_text_to_file(translated_zh_text, 'zh', filename)
        df = pd.read_csv(filename, index_col=0).reset_index(drop=True)
        df.to_csv(filename)
        print("Currently {} lines in {}".format(df.shape[0], filename))
        print(df['lang'].value_counts())

if __name__=="__main__":
    page = input("Enter starting page: ")
    starting_url = "https://en.wikipedia.org/wiki/"+page.capitalize()
    filename = '../data/{}.csv'.format(today_string)
    wide_scrape(starting_url, filename)
