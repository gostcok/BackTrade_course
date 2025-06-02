import yfinance as yf
import pandas as pd
import backtrader as bt

# ====== 抓台股資料：以台積電 (2330.TW) 為例 ======
def fetch_tw_stock(stock_id='2330.TW', start='2020-01-01', end='2024-12-31'):
    df = yf.download(stock_id, start=start, end=end)
    if isinstance(df.columns,pd.MultiIndex):
      df.columns = df.columns.droplevel(1)
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    df.dropna(inplace=True)
    df.reset_index(inplace=True)
    return df


# ====== 自訂 Feed 給 Backtrader 用 ======
class PandasData_BT(bt.feeds.PandasData):
    params = (
        ('datetime', 'Date'),
        ('open', 'Open'),
        ('high', 'High'),
        ('low', 'Low'),
        ('close', 'Close'),
        ('volume', 'Volume'),
        ('openinterest', -1),
    )


# ====== 策略：簡單均線交叉 ======
class MutiMAStrategy(bt.Strategy):
    params = (
        ('ma_short', 5),
        ('ma_long', 20),
    )

    def __init__(self):
        self.ma_short_list=[]
        self.ma_long_list=[]
        self.trade_count={data._name:0 for data in self.datas}

        for data in self.datas:
            ma_short=bt.ind.SMA(data.close,period=self.params.ma_short)
            ma_long=bt.ind.SMA(data.close,period=self.params.ma_long)
            self.ma_short_list.append(ma_short)
            self.ma_long_list.append(ma_long)

    def next(self):
        for i,data in enumerate(self.datas):
            pos=self.getposition(data).size
            name=data._name
            if not pos:
                if self.ma_short_list[i][0] > self.ma_long_list[i][0]:
                    self.buy(data=data)
                    self.trade_count[name]+=1
            else:
                if self.ma_short_list[i][0] < self.ma_long_list[i][0]:
                    self.close(data=data)
                    self.trade_count[name]+=1
    def stop(self):
        for name,count in self.trade_count.items():
            print(f"{name} 總交易次數: {count}")
# ====== 主程式 ======
if __name__ == '__main__':

    # 1. 抓資料
    symbols=['2330.TW', '2317.TW', '2454.TW']  # 台積電、鴻海、聯發科等

    cerebro = bt.Cerebro()

    for symbol in symbols:
        df = fetch_tw_stock(symbol)
        data=PandasData_BT(dataname=df)
        cerebro.adddata(data, name=symbol)
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='ta')

    cerebro.broker.setcash(1000000)  # 設定初始資金
    cerebro.addstrategy(MutiMAStrategy)
    result=cerebro.run()
    # # cerebro.plot(style='candlestick')  # 繪製圖表
    # strat=result[0]
    # print(strat.analyzers.ta.get_analysis().total.get('total'))  # 總交易次數