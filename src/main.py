import os
from const import RESOURCE_ROOT

proxy = set()
with open(os.path.join(RESOURCE_ROOT, 'https_proxy'), 'r') as f:
	for line in f.readlines():
		proxy.add(line.strip())
proxy = [{'https': p} for p in proxy]

import stock
fetcher = stock.TwseFetcher(proxy)
df = stock.StockInfoGetter.get_stock(fetcher, 2020, 11)
import pickle
pickle.dump(df, open('df.pkl', 'wb'))

