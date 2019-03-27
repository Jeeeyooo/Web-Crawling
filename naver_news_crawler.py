# naver news crawling
# 네이버 뉴스 검색을 통해 특정 쿼리들을 입력하고 현재로부터 얼마나 이전의 날짜까지 수집해올지 지정하면
# 날짜, 검색어, 뉴스 제목, 뉴스 요약, 뉴스 url들을 각각 list형태로 반환하여,
# dataFrame 형태로 쉽게 변환한 뒤 csv파일로 저장하는 코드입니다.

from bs4 import BeautifulSoup as bs
import requests #HTTP 요청을 보내는 모듈 
import re #정규 표현식 사용하기 위한 모듈
import pandas as pd

from time import strftime
from datetime import datetime, timedelta


def news_crawler (queries, _ago = 30 ):
  
    header = { 

        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36' 

    } 
    
    
    # 날짜 리스트 만들기
    dates = []
    fromtos = []
    
    now_date = datetime.now().date()
    
    for i in range(0, _ago):
        day = timedelta(days=i)
        _date = (now_date - day).strftime("%Y.%m.%d")
        dates.append(_date)
        _fromto = _date.replace(".","") 
        fromtos.append(_fromto)
        #print(_date + " "*5 + _fromto)
        
    # url 리스트 만들기 & 거기에 매칭되는 쿼리 리스트
    urls_without_page = []
    queries_for_mapping = []
    
    for query in queries:
        for(_date, _fromto) in zip(dates, fromtos):
            url = "https://search.naver.com/search.naver?where=news&query="+query+"&sort=1&field=1&ds=" \
            +_date+"&de="+_date +"&nso=so%3Ar%2Cp%3Afrom"+_fromto+"to"+_fromto+"%2Ca%3A&start=" 
            urls_without_page.append(url)
            queries_for_mapping.append(query)
            #print(url + " "*20 + query)
    
    # 크롤링
    date_list = []
    query_list = []
    summary_list = []
    url_list = []
    title_list = []
    
    for (_url, _date, query) in zip(urls_without_page, dates, queries_for_mapping):
        
        date = _date.replace(".","-")
        print(date)
        
        
        page = 1
        
        while True:
            print(page)
            
            url = _url + str(page)
            print(url)
            print("-"*30)
            
            req = requests.get(url, headers=header)
            
            if req.status_code != 200:
                print("REQ ERR")
                return -1
            
            cont = req.content
            soup = bs(cont, 'html.parser')
            
            if soup.findAll("a",{"class":"_sp_each_url"}) == [] :
                break 

            # 요약본 찾기
            for (dd, i) in zip(soup.findAll("dd"), range(1,len(soup.findAll("dd"))+1)):
                #print("##"*20 + "  "+str(i)+"  " + "##"*20)
                #print(summary.prettify())

                if i>=6 and not i%2:
                    summary = dd.get_text()
                    #print(summary)
                    summary_list.append(summary)


            # 링크 찾기 
            for urls in soup.findAll("a",{"class":"_sp_each_url"}): 

                # dailysecu는 링크가 이상해.. 서 https:붙여줘야함
                if urls.attrs["href"]: #.startswith("https://news.naver.com"): 
                    link = urls.attrs["href"]

                    if "dailysecu" in link:
                        link = "https:"+link

                    url_list.append(link)
                    #print(link)

                    
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
    

date, query, title, summary = news_crawler(['test'],7) #test에 대해 검색하는 내용을 현재로부터 7일전까지 받아와서 저장 
    
   
data = { "date" : date,
        "query": query,
        "title" : title,
        "summary" : summary,
        "url" : url
       }

df = pd.DataFrame(data)
df


fname = "crawling_output_test.csv"

df.to_csv(fname, header=True, index=False)
