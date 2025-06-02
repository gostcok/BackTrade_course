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
class MAStrategy(bt.Strategy):
    params = (
        ('ma_short', 5),
        ('ma_long', 20),
    )

    def __init__(self):
        self.ma_short = bt.ind.SMA(period=self.params.ma_short)
        self.ma_long = bt.ind.SMA(period=self.params.ma_long)

    def next(self):
        if not self.position:
            if self.ma_short[0] > self.ma_long[0]:
                self.buy()
        else:
            if self.ma_short[0] < self.ma_long[0]:
                self.close()


# ====== 主程式 ======
if __name__ == '__main__':
    # 1. 抓資料
    df = fetch_tw_stock()

    # 2. 建立 Backtrader
    cerebro = bt.Cerebro()
    data = PandasData_BT(dataname=df)

    # 加入策略：會測試 fast=5~10 & slow=15~25 的所有組合
    cerebro.optstrategy(
        MAStrategy,
        ma_short=range(3, 5),  # 快速均線範圍
        ma_long=range(20, 22)   # 慢速均線範圍
    )

    # 3. 加入資料和策略
    cerebro.adddata(data)
    cerebro.broker.set_cash(1000000)
    cerebro.addsizer(bt.sizers.PercentSizer, percents=10)

    # 4. 跑策略
    print(f"Starting Portfolio Value: {cerebro.broker.getvalue():,.0f}")
    results=cerebro.run(optreturn=False)
    print(f"Final Portfolio Value: {cerebro.broker.getvalue():,.0f}")


    import csv

    # 5. 儲存結果到 CSV

    with open('opr_results.csv', 'w', newline='') as f:
        writer=csv.writer(f)
        writer.writerow(['ma_short', 'ma_long', 'final_value'])

        for result in results:
            strat = result[0]  # 每組參數回傳的 list 中第一個策略實例
            ma_short=strat.params.ma_short
            ma_long=strat.params.ma_long
            final= strat.broker.getvalue()
            writer.writerow([ma_short, ma_long, final])

