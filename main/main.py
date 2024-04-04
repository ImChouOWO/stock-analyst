from selenium import webdriver
import requests
import pandas as pd
import json
import yfinance as yf


class Stocker:
    def __init__(self,stock_list:list) -> None:
        self.stock_list = stock_list
        self.stock_data = None
        self.review_days = 5
        self.hitory_data = None
    def get_data(self):
        stock_id = None
        print(self.stock_list)
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
        res  = requests.get(url)

        # 判斷該API呼叫是否成功
        if res.status_code != 200:
            raise Exception('取得股票資訊失敗.')
        else:
            self.stock_data = json.loads(res.text)
            print(res.text)
            print("fetch sucess")
    def df_format(self):
        if self.stock_data != None:
            columns = ['c','n','z','tv','v','o','h','l','y', 'tlong']
            df = pd.DataFrame(self.stock_data['msgArray'], columns=columns)
            df.columns = ['股票代號','公司簡稱','成交價','成交量','累積成交量','開盤價','最高價','最低價','昨收價', '資料更新時間']
            print(df.head(10))
            return df
        else:
            return "No data get"
    def get_history(self):
        main_df = pd.DataFrame()
        for id in self.stock_list:
            try:
                data = yf.Ticker(id +".TW")
                new_data = data.history(period="max").tail(self.review_days)
                if main_df.empty:
                    main_df = new_data
                else:
                    main_df = pd.concat([main_df, new_data])
            except:
                print("yf erro check for id list")

            
if __name__ == "__main__":
    stocker  = Stocker(['0050', '0056', '2330', '00940', '1216'])
    stocker.get_data()
    stocker.df_format()
    stocker.get_history()