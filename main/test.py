
import yfinance as yf
import pandas as pd
stock_id_tse = ['0050', '0056', '2330', '2317', '1216']
stock_id = stock_id_tse[0]+ stock_id_tse[1]+'.TW'
data = yf.Ticker(stock_id)
df = data.history(period="max")
print(df)