## Current Version 1.2.1
## Craigslist_Scraper 1.2.1  --  increase data storing time and fixed duplicate issue
## Craigslist_Scraper 1.1.1  --  Sending email as HTML
## Craigslist_Scraper 1.1.0  --  Add system argument for sleep time

import datetime
import os
import re
import sqlite3
import time
from subprocess import Popen

import pandas as pd
import requests
from parsel.selector import Selector
from multiprocessing.pool import Pool
from tqdm import tqdm

import smtplib
import email.message
import argparse

##Configs
smtp_email = 'sales@unixcommerce.com'
smtp_pass = 'ncpjsalbdbkklhpm'
smtp_host = 'smtp.gmail.com'
smtp_port = 587
# receiver_address = 'hwtsvjpnzmzgfh@emergentvillage.org'
receiver_address = 'abidbd1249@gmail.com'
# receiver_address = 'sales@unixcommerce.com'

delay = 8
##Input
input_folder = 'Input'
os.makedirs(input_folder, exist_ok=True)
input_file_name = 'input.csv'
input_file_path = os.path.join(input_folder, input_file_name)

##Database
database_folder = 'Database'
os.makedirs(database_folder, exist_ok=True)
database_filename = "Craigslist.db"
database_table_name = 'Craigslist'
database_path = os.path.join(database_folder, database_filename)
con = sqlite3.connect(database_path)
cur = con.cursor()
query_create_table = "CREATE TABLE if not exists Craigslist(timestamp, url, isMatch)"
cur.execute(query_create_table)
cur.close()

headers = {'user-agent': 'Opera/9.80 (iPhone; Opera Mini/8.0.0/34.2336; U; en) Presto/2.8.119 Version/11.10'}
main_list = {}
target_text = ''.join(
    re.findall(r'[\w]+', "it's ok to contact this poster with services or other commercial interests")).lower()


def Page_Parser(Url, Proxy):
    res = requests.get(Url, proxies=Proxy, headers=headers)
    if res.status_code == 200:
        time.sleep(delay)
        page_select = Selector(res.text)
        txt = page_select.xpath('//ul[@class="notices"]/li/text()').get()
        t_text = ''.join(re.findall(r'[\w]+', txt)).lower()
        if target_text == t_text:
            return {Url: True}
        else:
            return {Url: False}
    else:
        print('Maybe Ip blocked')
        return {}


def Listing_Parser(Url):
    res = requests.get(Url, headers=headers)
    if res.status_code == 200:
        page_select = Selector(res.text)
        return [i.strip() for i in page_select.xpath('////li[@class="result-row"]/a/@href').getall() if i.strip()]
    return []


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-s", "--sleep")
    sleep_time = arg_parser.parse_args().sleep
    if sleep_time:
        print("Sleep time set :", sleep_time)
        sleep_time = int(sleep_time)
    else:
        sleep_time = 5
        print("Sleep time set :", sleep_time)
    main_df = pd.read_sql(f'Select * from {database_table_name}', con)
    monthInSeconds = 2678400
    time_stamp = datetime.datetime.now().timestamp()
    main_df.drop_duplicates(subset=['url'], inplace=True)
    main_df = main_df[main_df['timestamp'] >= time_stamp - monthInSeconds]
    main_df_urls = main_df['url'].to_list()
    print("Database urls length :", len(main_df))
    message = email.message.Message()
    message['From'] = smtp_email
    message['To'] = receiver_address
    message['Subject'] = 'Craigslist Scraper'
    message.add_header('Content-Type', 'text/html')
    message.set_payload('Matched Url<br> <a href={}>{}</a>')

    user = 'username'  ## username of your proxy service
    password = 'password'  ## password of your proxy service
    hostname = 'hostname'  ## hostname or IP of your proxy service
    port = 'port'  ## port or IP of your proxy service
    proxy = f'http://{user}:{password}@{hostname}:{port}'
    proxy_on = False  ## Please turn it on after fillup the proxy credentials, otherwise scraper will not run
    try:
        if not proxy_on:
            proxies = ''
        else:
            proxies = {'http': proxy, 'https': proxy}
        input_urls = pd.read_csv(input_file_path)['url'].to_list()
        for input_url in input_urls:
            with Pool() as pool:
                urls = [i for i in Listing_Parser(input_url) if i not in main_df_urls]
                print(f"Listing urls {len(urls)} :", urls)
                if urls:
                    progress = tqdm(total=len(urls), unit=' urls')
                    results = [pool.apply_async(Page_Parser, args=(url, proxies)) for url in urls]
                    pool.close()
                    for num, result in enumerate(results):
                        main_list.update(result.get())
                        progress.update(1)
                    print('\n' * 3)
                    sending_list = []
                    for m_url in main_list:
                        main_df = pd.concat([main_df, pd.DataFrame(columns=['timestamp', 'url', 'isMatch'],
                                                                   data=[[time_stamp, m_url, main_list[m_url]]])])
                        if main_list.get(m_url) and m_url not in main_df_urls:
                            sending_list.append(m_url)
                    print(f"Urls for sending Mail {len(sending_list)} : ", sending_list)
                    for url in sending_list:
                        session = smtplib.SMTP(smtp_host, smtp_port)
                        session.starttls()
                        session.login(smtp_email, smtp_pass)
                        session.sendmail(smtp_email, receiver_address, message.as_string().format(url, url))
                        session.quit()
            print("\n" * 3, f'Sleeping for {sleep_time} seconds')
            time.sleep(sleep_time)
        print("Mail send")
        main_df.to_sql(database_table_name, con=con, if_exists='replace', index=False)
        Popen(['sudo', 'chmod', '-R', '775', database_path])
    except KeyboardInterrupt:
        print("Force stopping the scraping process, Saving the database")
        main_df.to_sql(database_table_name, con=con, if_exists='replace', index=False)
        Popen(['sudo', 'chmod', '-R', '775', database_path])
        print("Database updated and fixed the permission")