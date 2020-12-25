import os
import pickle
import time
import itertools
from collections import namedtuple

import pandas as pd
import twstock as ts
import requests as rq

__all__ = ['get_twse', 'StockInfoGetter', 'TwseFetcher']

from const import RESOURCE_ROOT

PATH_STOCK_INFO = os.path.join(RESOURCE_ROOT, 'stock_info.h5')
PATH_STOCK = os.path.join(RESOURCE_ROOT, 'stock.h5')


def get_h5_key_name(year, month):
    return f'{year:4d}{month:2d}'


def get_h5_name(year, month):
    return os.path.join(RESOURCE_ROOT, f'stock{get_h5_key_name(year, month)}.h5')


class Fetcher:
    def __init__(self, proxy):
        self._proxy = proxy
        self._head = 0
        self._cnt = 0
        self._sleep_time = 0
        self._proxy_avail = {pxy['https']: 0 for pxy in proxy}
        self._err = {}
    def prepare_proxy(self):
        self._cnt = 0
        self._sleep_time = 0
        self._err = {}

    def get_proxy(self):
        if self._cnt != 0 and self._cnt % len(self._proxy) == 0:
            print(f'trial time = {self._cnt}')
            print('\n'.join(f'{k}: {v}' for k, v in self._err.items()))
            self._sleep_time += 10.0 ** (self._cnt / len(self._proxy))
            print(f'sleep time increased to {self._sleep_time}')
        time.sleep(self._sleep_time)
        p = self._proxy[self._head]
        self._head = (self._head + 1) % len(self._proxy)
        self._cnt += 1
        return p

    def purify(r):
        print('not implemented')

    def get_data_from_https_request(self, q, params=None, retry_time=10):
        self.prepare_proxy()
        for t in range(retry_time):
            pxy = self.get_proxy()
            for i in range(20):
                try:
                    r = rq.get(q, params=params, timeout=1, proxies=pxy)
                    data = self.purify(r)
                    self._proxy_avail[pxy['https']] += 1
                    print('proxy availability')
                    print('\n'.join(f'{k}: {v}' for k, v in self._proxy_avail.items()))
                    return data
                except Exception as e:
                    print(f'Error occur: {e}')
                    if str(e) not in self._err:
                        self._err[str(e)] = 1
                    else:
                        self._err[str(e)] += 1
                print('.', end='')
            print('')

DATATUPLE = namedtuple('Data', ['date', 'capacity', 'turnover', 'open',
                                'high', 'low', 'close', 'change', 'transaction'])


class TwseFetcher(Fetcher):
    TWSE_URL = 'https://www.twse.com.tw/exchangeReport/STOCK_DAY?datexchangeReport/STOCK_DAY'
    def get_stock(self, sid, year, month):
        params = {'stockId': sid, 'date': '%d%2d01' % (year, month)}
        return self.get_data_from_https_request(self.TWSE_URL, params=params)

    def purify(self, r):
        data = r.json()
        if data['stats'] == 'OK':
            data['data'] = [self._make_datatuple(d) for d in data['data']]
        else:
            data['data'] = []
        return data

    def _make_datatuple(self, data):
        data[0] = datetime.datetime.strptime(self._convert_date(data[0]), '%Y/%m/%d')
        data[1] = int(data[1].replace(',', ''))
        data[2] = int(data[2].replace(',', ''))
        data[3] = None if data[3] == '--' else float(data[3].replace(',', ''))
        data[4] = None if data[4] == '--' else float(data[4].replace(',', ''))
        data[5] = None if data[5] == '--' else float(data[5].replace(',', ''))
        data[6] = None if data[6] == '--' else float(data[6].replace(',', ''))
        # +/-/X表示漲/跌/不比價
        data[7] = float(0.0 if data[7].replace(',', '') ==
                        'X0.00' else data[7].replace(',', ''))
        data[8] = int(data[8].replace(',', ''))
        return DATATUPLE(*data)

    def purify(self, original_data):
        return [self._make_datatuple(d) for d in original_data['data']]

class StockInfoGetter:
    _TWSE = None

    @classmethod
    def get_twse(cls):
        if not os.path.exists(PATH_STOCK_INFO):
            cls._TWSE = pd.DataFrame.from_dict(ts.twse, orient='index')
            cls._TWSE.to_hdf(PATH_STOCK_INFO, 'twse')
        if cls._TWSE is None:
            cls._TWSE = pd.read_hdf(PATH_STOCK_INFO, 'twse')
        return cls._TWSE

    @classmethod
    def get_stock(cls, fetcher, year, month):
        path = get_h5_name(year, month)
        if not os.path.exists(path):
            stock_code_dtype = pd.CategoricalDtype(cls.get_twse().index)
            todo = set(cls.get_twse().index)
            if os.path.exists(f'{path}.done.pkl'):
                df_s, done = pickle.load(open(f'{path}.done.pkl', 'rb'))
            else:
                df_s = []
                done = set()
                pickle.dump((df_s, done), open(f'{path}.done.pkl', 'wb'))
            todo = todo.difference(done)

            for i, stock_code in enumerate(todo):
                stock = fetcher.get_stock(stock_code, year, month)
                df_s.append(pd.DataFrame(stock))
                df_s[-1]['code'] = pd.Series(stock_code, index=df_s[-1].index, dtype=stock_code_dtype)
                done.add(stock_code)
                print(f'{stock_code} -- {100*len(done)/len(cls.get_twse().index):g}%')
                pickle.dump((df_s, done), open(f'{path}.done.pkl', 'wb'))

            df = pd.concat(df_s)
            df.set_index(['code', 'date'])
            df.to_hdf(path, get_h5_key_name(year, month))
        else:
            df = pd.read_hdf(path, get_h5_key_name(year, month))
        return df


def get_twse():
    return StockInfoGetter.get_twse()
