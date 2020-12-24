proxy = set()
with open('https_proxy', 'r') as f:
	for line in f.readlines():
		proxy.add(line.strip())
proxy = [{'https': p} for p in proxy]

import stock
fetcher = TwseFetcher(proxy)
df = stock.StockInfoGetter.get_stock(fetcher, 2020, 11)
import pickle
pickle.dump(df, open('df.pkl', 'wb'))

