import os
import pickle
import time

import pandas as pd
import twstock as ts

__all__ = ['get_twse', 'StockInfoGetter']

from const import RESOURCE_ROOT
from windscribe import WindscribeVpn, WindscribeException

PATH_STOCK_INFO = os.path.join(RESOURCE_ROOT, 'stock_info.h5')
PATH_STOCK = os.path.join(RESOURCE_ROOT, 'stock.h5')


def get_h5_key_name(year, month):
    return f'{year:4d}{month:2d}'


def get_h5_name(year, month):
    return os.path.join(RESOURCE_ROOT, f'stock{get_h5_key_name(year, month)}.h5')


class StockInfoGetter:
    _TWSE = None
    _vpn = WindscribeVpn()

    @classmethod
    def _change_vpn(cls):
        while True:
            try:
                cls._vpn.change_vpn_via_windscribe()
            except WindscribeException as e:
                print(e)
                print('sleep for 5 seconds')
                time.sleep(5)
            try:
                cls._vpn.login_windscribe()
            except WindscribeException as e:
                print(e)
                print('sleep for 5 seconds')
                time.sleep(5)

    @classmethod
    def get_twse(cls):
        if not os.path.exists(PATH_STOCK_INFO):
            cls._TWSE = pd.DataFrame.from_dict(ts.twse, orient='index')
            cls._TWSE.to_hdf(PATH_STOCK_INFO, 'twse')
        if cls._TWSE is None:
            cls._TWSE = pd.read_hdf(PATH_STOCK_INFO, 'twse')
        return cls._TWSE

    @classmethod
    def get_stock(cls, year, month):
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
                try:
                    stock = ts.Stock(stock_code, initial_fetch=False).fetch(year, month)
                    df_s.append(pd.DataFrame(stock))
                    df_s[-1]['code'] = pd.Series(stock_code, index=df_s[-1].index, dtype=stock_code_dtype)
                    done.add(stock_code)
                    print(f'{stock_code} -- {100*len(done)/len(cls.get_twse().index):g}%')
                    pickle.dump((df_s, done), open(f'{path}.done.pkl', 'wb'))
                except ConnectionError as e:
                    print(e)
                    cls._change_vpn()
                except Exception as e:
                    print(e)
                    cls._change_vpn()

            df = pd.concat(df_s)
            df.set_index(['code', 'date'])
            df.to_hdf(path, get_h5_key_name(year, month))
        else:
            df = pd.read_hdf(path, get_h5_key_name(year, month))
        return df


def get_twse():
    return StockInfoGetter.get_twse()
