import yfinance as yf
import pandas as pd
import backtrader as bt
import matplotlib.pyplot as plt

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
class MAStrategy(bt.Strategy):
    params = (
        ('ma_short', 5),
        ('ma_long', 20),
    )

    def __init__(self):
        self.ma_short = bt.ind.SMA(period=self.params.ma_short)
        self.ma_long = bt.ind.SMA(period=self.params.ma_long)
        self.starting_cash = None

    def start(self):
        self.starting_cash = self.broker.getvalue()

    def stop(self):
        self.final_cash = self.broker.getvalue()

    def next(self):
        if not self.position:
            if self.ma_short[0] > self.ma_long[0]:
                self.buy()
        else:
            if self.ma_short[0] < self.ma_long[0]:
                self.close()


# ====== 主程式 ======
if __name__ == '__main__':
    # 載入資料
    df = fetch_tw_stock()
    data = PandasData_BT(dataname=df)

    # 建立 cerebro
    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    cerebro.addstrategy(MAStrategy)
    cerebro.broker.set_cash(1000000)
    cerebro.addanalyzer(bt.analyzers.TimeReturn,_name='returns')# 🔥 加入日報酬分析器

    # 執行
    result=cerebro.run(optreturn=False)
    strat=result[0]  # 取得策略結果

    ##取得資金曲線
    daily_returns=strat.analyzers.returns.get_analysis()  # 🔥 取得日報酬分析結果
    returns_series=pd.Series(daily_returns)

    # 折線圖：累積報酬
    equity_curve = (1 + returns_series).cumprod() * 1000000  # 折現乘上初始資金

    plt.figure(figsize=(10, 5))
    plt.plot(equity_curve,label='Equity Curve')
    plt.title('Equity Curve')
    plt.xlabel('Date')
    plt.ylabel('Portfolio Value')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

