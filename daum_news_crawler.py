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
    dates_for_mapping = []

    # url list & 거기에 매칭되는 쿼리 리스트
    for query in queries:
        for (sd, ed) in zip (s_dates, e_dates):

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
            dates_for_mapping.append(sd)



    # 크롤링
    date_list = []
    query_list = []
    summary_list = []
    url_list = []
    title_list = []

    p_idx = urls_without_page[0].find('page')





    for (_url, _date, query) in zip(urls_without_page, dates_for_mapping, queries_for_mapping):
        date = _date[:4] + "-" + _date[4:6] + "-" + _date[6:8]
        

        page = 1

        while True:

            url = _url[:p_idx] + str(page) + _url[p_idx+4:]


            soup = request_soup(url)

            div_soup = soup.findAll("div", {"class" : "wrap_tit mg_tit"})
            span_soup = soup.findAll("span", {"class": "f_nb date"})
            desc_soup = soup.findAll("p", {"class":"f_eb desc"})
            end_soup = soup.findAll("div", {"class":"result_message mg_cont"})

            nothing_soup = soup.findAll("strong", {"class":"tit"});

            
            for (span,div, desc) in zip(span_soup, div_soup, desc_soup):

                dd = div.findAll("a", {"class":"f_link_b"})



                for d in dd:

                    title_list.append(d.get_text())
                    url_list.append(d.attrs['href'])
                    date_list.append(date)
                    query_list.append(query)
                    summary_list.append(desc.get_text())
            
            if end_soup:
                end = end_soup[0].get_text()
                break
            
            if nothing_soup:
                nothing = nothing_soup[0].get_text()
                break

            page += 1
    

    return date_list, query_list, title_list, summary_list, url_list



   
date, query, title, summary, url = news_crawler(['IoT'], 7)
   
   
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
