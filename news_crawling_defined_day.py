# handler.py

# for Crawling
from bs4 import BeautifulSoup as bs
import requests
import pandas as pd

from time import strftime
from datetime import datetime, timedelta
from random import shuffle

# for AWS
import json
import os
import pymysql as mysql


conn = mysql.connect(host=os.environ['DB_HOST'], user=os.environ['USER'], password=os.environ['DB_PW'], db = os.environ['DB_NAME'])




def create_conn():
    return mysql.connect(host=DB_HOST, user=DB_USER, password=DB_PW, db = DB_NAME)



def main(event, context):
    query = event['query']
    date = event['date']

    date_list, query_list, title_list, summary_list, url_list = naver_news_crawler(query, date) # return new file name

    naver = upload_to_DB(date_list,query_list,title_list,summary_list,url_list)

    date_list, query_list, title_list, summary_list, url_list = daum_news_crawler(query, date) # return new file name


    daum = upload_to_DB(date_list,query_list,title_list,summary_list,url_list)

     
    return {
        'statusCode' : 200,
        'body' : json.dumps([naver, daum])
    }

def upload_to_DB(_date_list, _query_list, _title_list, _summary_list, _url_list):
    
    # DB 관련
    conn = create_conn()
    curs = conn.cursor()
     
    # 셔플링 (날짜까지 고려는 안함)
    random_list = list(range(0, len(_date_list)))
    shuffle(random_list)

    date_list = []
    query_list = []
    title_list = []
    summary_list = []
    url_list = []

    curs = conn.cursor()

    for random in random_list:
        date_list.append(_date_list[random])
        query_list.append(_query_list[random])
        title_list.append(_title_list[random])
        summary_list.append(_summary_list[random])
        url_list.append(_url_list[random])
    

    # 업로드
    for date, query, title, summary, url in zip(date_list, query_list, title_list, summary_list, url_list):
        sql = "INSERT IGNORE INTO news (upload_date, date, query, title, summary, url) VALUE ( %s, %s, %s, %s, %s, %s);"

        now_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        params = (now_date, date, query, title, summary, url)

        try :
            curs.execute(sql, params)
        except mysql.err.ProgrammingError as err:
            print("ERROR : {}".format(err))

    conn.commit()
    curs.close()
    del curs

    conn.close()
    del conn
    
    return 'success'

def request_soup(url):
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36' 
    }

    req = requests.get(url, headers=header)
    
    if req.status_code != 200:
        print("REQ ERR")
        return -1

    cont = req.content

    soup = bs(cont, 'html.parser')
    
    return soup


def daum_news_crawler(queries, defined_date):
    
    s_date = defined_date + '000000'
    e_date = defined_date + '235959'


    
    urls_without_page = []
    queries_for_mapping = []
    dates_for_mapping = []

    # url list & 거기에 매칭되는 쿼리 리스트
    for query in queries:
        url = 'https://search.daum.net/search?w=news&sort=recency&q='\
            +query\
            +'&cluster=n&DA=STC&s=NS&a=STCF&dc=STC&pg=1&r=1&p='\
            +'page'\
            +'&rc=1&at=more&sd='\
            + s_date\
            +'&ed='\
            + e_date\
            + '&period=u'

        urls_without_page.append(url)
        queries_for_mapping.append(query)
        dates_for_mapping.append(s_date)



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



def naver_news_crawler (queries, defined_date ):


    date = defined_date[0:4] + "." + defined_date[4:6] + "." + defined_date[6:8]
    fromto = defined_date

    #print(_date + " "*5 + _fromto)

    # url 리스트 만들기 & 거기에 매칭되는 쿼리 리스트
    urls_without_page = []
    queries_for_mapping = []
    dates_for_mapping = []


    for query in queries:
        url = "https://search.naver.com/search.naver?where=news&query="+query+"&sort=1&field=1&ds=" \
        +date+"&de="+date +"&nso=so%3Ar%2Cp%3Afrom"+fromto+"to"+fromto+"%2Ca%3A&start="
        
        urls_without_page.append(url)
        queries_for_mapping.append(query)
        dates_for_mapping.append(date)
            #print(url + " "*20 + query)

    # 크롤링
    date_list = []
    query_list = []
    summary_list = []
    url_list = []
    title_list = []

    for (_url, _date, query) in zip(urls_without_page, dates_for_mapping, queries_for_mapping):

        date = _date.replace(".","-")

        page = 1

        while True:

            url = _url + str(page)

            soup = request_soup(url)

            if soup.findAll("a",{"class":"_sp_each_url"}) == [] :
                break

            # 요약본 찾기
            for (dd, i) in zip(soup.findAll("dd"), range(1,len(soup.findAll("dd"))+1)):

                if i>=6 and not i%2:
                    summary = dd.get_text()
                    summary_list.append(summary)


            # 링크 찾기
            for urls in soup.findAll("a",{"class":"_sp_each_url"}):

                # dailysecu는 링크가 이상해서 https:붙여줘야함
                if urls.attrs["href"]: #.startswith("https://news.naver.com"):
                    link = urls.attrs["href"]

                    if "dailysecu" in link:
                        link = "https:"+link

                    url_list.append(link)


            # 제목 찾기 & 날짜 append & 쿼리 append
            _titles = soup.findAll("dt")

            for (_title, i) in zip(_titles, range(1,len(_titles)+1)):
                _title_a = _title.findAll("a")
                if len(_title_a):
                    title = _title_a[0].get("title")
                    if title:
                        #print(title)
                        title_list.append(title)
                        date_list.append(date)
                        query_list.append(query)

            page += 10


    return date_list, query_list, title_list, summary_list, url_list

    





if __name__ == "__main__":
    main('', '')

