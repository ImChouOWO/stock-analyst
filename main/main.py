from selenium import webdriver
import requests
import pandas as pd
import json
import yfinance as yf
import numpy as np
import time
import os
from bs4 import BeautifulSoup
from openai import OpenAI


class Stocker:

    def __init__(self,stock_list:list) -> None:
        self.stock_list = stock_list
        self.review = 5

        # dataframe format
        self.stock_data = None
        self.history_data = None 
        self.market_close_data = None
        self.news_data = None
        self.unusual_info_data = None
        self.prompt = None

    
    def fetch_data(self,url:str):
        res = requests.get(url)
        # 判斷該API呼叫是否成功
        if res.status_code != 200:
            raise Exception('取得訊失敗.')
        else:
            print("fetch sucess")  
            return json.loads(res.text)
  
  
    def get_data(self):
        stock_id = None
       
        try:
            if len(self.stock_list) != 0:
                stock_id = "|".join(map(lambda x:f"tse_{x}.tw",self.stock_list))
                print(stock_id)
            else:
                stock_id = f"tes_{stock_id}.tw"
        except:
            print("failed to get data")

        if stock_id == None:
            print("ID not set")
            return

        url = f'https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={stock_id}'
        data = self.fetch_data(url)
        columns = ['c','n','z','tv','v','o','h','l','y', 'tlong']
        self.stock_data = pd.DataFrame(data['msgArray'], columns=columns)
        self.stock_data.columns = ['股票代號','公司簡稱','成交價','成交量','累積成交量','開盤價','最高價','最低價','昨收價', '資料更新時間']
        print(self.stock_data.head())


    def get_history(self):
        main_df = pd.DataFrame()
        for id in self.stock_list:
            try:
                data = yf.Ticker(id +".TW")
                new_data = data.history(period="max").tail(self.review)
                if main_df.empty:
                    main_df = new_data
                else:
                    main_df = pd.concat([main_df, new_data])

                    self.history_data = main_df
            except:
                print("yf erro check for id list")

    
                 
    def get_news(self):
        url = "https://openapi.twse.com.tw/v1/news/newsList"
        data = self.fetch_data(url)
        self.news_data = pd.DataFrame(data)[['Title']].head(self.review) 
        print(self.news_data.head())

    def market_close(self):
        url = "https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX"
        data = self.fetch_data(url)
        self.market_close_data = pd.DataFrame(data)
        print(self.market_close_data.head())

    def unusual_info(self):
        # 異常推介
        url = "https://openapi.twse.com.tw/v1/Announcement/BFZFZU_T"
        data = self.fetch_data(url)
        self.unusual_info_data = pd.DataFrame(data)
        self.unusual_info_data.columns = ["編號","股票代號","股票名稱","日期"]

        if self.unusual_info_data.iloc[0]['股票代號'] == "":
            self.unusual_info_data = "尚未提供資料"

        print(self.unusual_info_data)

    def read_file(self,file_path):
        with open(file_path,"r") as file:
            return file.read()


    def dataframe_to_txt(self):
        dataframes = [self.stock_data,
                      self.history_data,
                      self.market_close_data,
                      self.news_data,
                      self.unusual_info_data]
        
        names = ["個股資料",
                 "個股歷史資訊",
                 "大盤昨日資訊",
                 "台灣證券會近日新聞",
                 "異常推介"]
       
        directory = "data"
        file_name = f"{time.strftime('%Y-%m-%d')}.txt"
        file_path = f"{directory}/{file_name}"
        os.makedirs(directory,exist_ok=True)
       
        with open(file_path,"w") as file:
            for i,df in enumerate(dataframes):
                try:
                    df_string = df.to_string()
                except:
                    df_string=df
                file.write(f"DataFrame {names[i]}:\n{df_string}\n\n")
        
        txt_content = self.read_file(file_path)
        self.prompt = f'{self.stock_list}的相關走勢，以下是個股的相關資訊，{txt_content}'
    

    

    def fetch_news_web(self,url,class_name,web_tag):
        res = requests.get(url)
        res.raise_for_status()

        try:
            soup = BeautifulSoup(res.content,"lxml")
            if class_name:
                elements = soup.find_all(web_tag,class_name)
            else:
                elements = soup.find_all(web_tag)
            
        except:
            elements = "fetch fail"

        return elements  


    def news_format(self,search_text_list:list,web_tag:str,class_name:str,directory:str):
    
        for search_text in search_text_list:

            url = f"https://tw.news.yahoo.com/search?p={search_text}"
            get_elements = self.fetch_news_web(url=url,class_name=class_name,web_tag=web_tag)
            data = []
            for element in get_elements:
                data.append(element.text.strip())

            news_df = pd.DataFrame(data)
            news_df.columns = ['title']

            self.save_dataframe(df=news_df,stock=search_text,directory=directory)
        
    def save_dataframe(self,df:pd.DataFrame,stock:str,directory:str):
      
        file_name = f"{stock}_{time.strftime('%Y-%m-%d')}_news.xlsx"
        file_path = f"{directory}/{file_name}"
        os.makedirs(directory,exist_ok=True)
        df.to_excel(file_path,index=False)
    
    def ask_gpt(self):
        client = OpenAI(
            api_key = "open_ai_api_key"
        )
        response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
            "role": "system",
            "content": "你現在是一個專業的股票分析師，會以我提供的資料為基礎回答我的問題，並在最後透過表格的方式將我詢問的股票以你分析的最佳進出場價格呈現出來"
            },
            {
            "role": "user",
            "content": f'{self.prompt}'
            }
        ],
        temperature=1,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
        )
    

    def main(self):
        # get form 臺灣證券交易所 OpenAPI
        self.get_data()
        self.get_news()
        self.market_close()
        self.unusual_info()

        # get form yfinance
        self.get_history()

        self.dataframe_to_txt()
        
        # get the news from Yahoo finace 
        self.news_format(search_text_list=self.stock_list ,web_tag="h3" ,class_name="Mb(5px)" ,directory="csv")
        

        # self.ask_gpt()
          
if __name__ == "__main__":
    stocker  = Stocker(['0050', '0056', '2330', '00940', '1216'])
    stocker.main()
    