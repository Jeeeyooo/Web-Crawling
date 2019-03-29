from bs4 import BeautifulSoup as bs
import requests #HTTP 요청을 보내는 모듈 
import pandas as pd

from time import strftime
from datetime import datetime, timedelta


def request_soup (url):
    header = { 

        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36' 

    } 
    
    req = requests.get(url, headers=header)
    #print(url)
    if req.status_code != 200:
        print("REQ ERR")
        return -1
    
    
    cont = req.content
        
    soup = bs(cont, 'html.parser')
    
    return soup
    
def news_crawler (queries, _ago = 30):


# 날짜 리스트 만들기
s_dates = []
e_dates = []

now_date = datetime.now().date()

for i in range(0, _ago):
    day = timedelta(days=i)
    s_date = (now_date - day).strftime("%Y%m%d") + '000000'
    s_dates.append(s_date)
    e_date = (now_date - day).strftime("%Y%m%d") + '235959'
    e_dates.append(e_date)
    #print(s_date + " " *5 + e_date)

urls_without_page = []
queries_for_mapping = []


# url list & 거기에 매칭되는 쿼리 리스트
for query in queries:
    for (sd, ed) in zip (s_dates, e_dates):
        url = 'https://search.daum.net/search?DA=PGD&a=STCF&at=more&cluster=n&dc=STC&ed=' + \
        e_date + '&https_on=on&p=page&period=d&pg=1&q=' +query+\
        '&r=1&rc=1&s=NS&sd=&sort=recency&w=news'

        url = 'https://search.daum.net/search?w=news&sort=recency&q='\
            +query\
            +'&cluster=n&DA=STC&s=NS&a=STCF&dc=STC&pg=1&r=1&p='\
            +'page'\
            +'&rc=1&at=more&sd='\
            + sd\
            +'&ed='\
            + ed\
            + '&period=u'

        urls_without_page.append(url)
        queries_for_mapping.append(query)

#print(queries_for_mapping)


# 크롤링
date_list = []
query_list = []
summary_list = []
url_list = []
title_list = []

p_idx = urls_without_page[0].find('page')
#print(p_idx)





for (_url, _date, query) in zip(urls_without_page, s_dates, queries_for_mapping):
    date = _date[:4] + "-" + _date[4:6] + "-" + _date[6:8]
    #print(query)

    page = 1

    while True:
        print("page : ",page)

        url = _url[:p_idx] + str(page) + _url[p_idx+4:]

        print(url)
        #print("---"*10)

        soup = request_soup(url)
        #print(soup.prettify())

        div_soup = soup.findAll("div", {"class" : "wrap_tit mg_tit"})
        span_soup = soup.findAll("span", {"class": "f_nb date"})
        desc_soup = soup.findAll("p", {"class":"f_eb desc"})
        end_soup = soup.findAll("div", {"class":"result_message mg_cont"})



        for (span,div, desc) in zip(span_soup, div_soup, desc_soup):

            dd = div.findAll("a", {"class":"f_link_b"})



            for (d,s) in zip(dd, desc):
                print(d.get_text()) #title
                print(d.attrs['href']) #link

                title_list.append(d.get_text())
                url_list.append(d.attrs['href'])
                date_list.append(date)
                query_list.append(query)
                summary_list.append(s)

        if end_soup:
            end = end_soup[0].get_text()
            print(end)
            break
        page += 1


return summary_list, url_list, title_list, date_list, query_list
    
   
 summary, url, title, date, query = news_crawler(['IoT'], 7)
   
   
data={
  "date" : date,
  "query" : query,
  "title" : title,
  "summary" : summary,
  "url" : url   
}

df = pd.DataFrame(data)

fname = "crawling_output_test.csv"
df.to_csv(fname, header=True, index=False)
