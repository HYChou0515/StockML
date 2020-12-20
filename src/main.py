import stock
df = stock.StockInfoGetter.get_stock(2020, 11)
import pickle
pickle.dump(df, open('df.pkl', 'wb'))

