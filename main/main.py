from selenium import webdriver
import requests
import pandas as pd
import json
import yfinance as yf
import numpy as np
import time
import os


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
    def fetch_data(self,url):
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
                                                                                                    
    def main(self):
        self.get_data()
        self.get_history()
        self.get_news()
        self.market_close()
        self.unusual_info()
        self.dataframe_to_txt()

          
if __name__ == "__main__":
    stocker  = Stocker(['0050', '0056', '2330', '00940', '1216'])
    stocker.main()
    