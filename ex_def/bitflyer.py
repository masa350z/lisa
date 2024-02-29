import urllib.parse
import requests
import hashlib
import json
import time
import hmac


class BitFlyer:
    def __init__(self, leverage=False, advantage=0, order_type='MARKET', api_key=None, api_secret=None):
        self.api_url = "https://api.bitflyer.jp"
        if leverage:
            self.product_code = 'FX_BTC_JPY'
        else:
            self.product_code = 'BTC_JPY'
        self.advantage = int(advantage)
        self.order_type = order_type
        self.api_key = api_key
        self.api_secret = api_secret

    def request(self, endpoint, method="GET", params=None):
        if method == "POST":
            body = json.dumps(params)
        else:
            if params:
                body = "?" + urllib.parse.urlencode(params)
            else:
                body = ""

        access_timestamp = str(time.time())
        api_secret = str.encode(self.api_secret)
        text = str.encode(access_timestamp + method + endpoint + body)
        access_sign = hmac.new(api_secret,
                                text,
                                hashlib.sha256).hexdigest()
        auth_header = {
            "ACCESS-KEY": self.api_key,
            "ACCESS-TIMESTAMP": access_timestamp,
            "ACCESS-SIGN": access_sign,
            "Content-Type": "application/json"
        }

        try:
            url = self.api_url + endpoint
            with requests.Session() as s:
                if auth_header:
                    s.headers.update(auth_header)

                if method == "GET":
                    response = s.get(url, params=params)
                else:  # method == "POST":
                    response = s.post(url, data=json.dumps(params))
            if not response.content.decode("utf-8") == '':
                content = json.loads(response.content.decode("utf-8"))

                return content
        except requests.RequestException as e:
            print(e)
            raise e

    def ticker(self):
        try:
            params = {'product_code': self.product_code}
            endpoint = "/v1/ticker"
            res = self.request(endpoint, params=params)
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('ticker')
            print(e)
            return 'E'

    def board(self):
        try:
            params = {'product_code': self.product_code}
            endpoint = "/v1/board"
            res = self.request(endpoint, params=params)
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('board')
            print(e)
            return 'E'

    def asset(self):
        try:
            if self.product_code == 'FX_BTC_JPY':
                endpoint = "/v1/me/getcollateral"
            else:
                endpoint = "/v1/me/getbalance"
            res = self.request(endpoint)
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('asset')
            print(e)
            return 'E'

    def position(self):
        try:
            params = {'product_code': 'FX_BTC_JPY'}
            endpoint = "/v1/me/getpositions"
            res = self.request(endpoint, params=params)
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('position')
            print(e)
            return 'E'

    def order(self, params):
        try:
            endpoint = "/v1/me/sendchildorder"
            res = self.request(endpoint, "POST", params=params)
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('order')
            print(e)
            return 'E'

    def get_price(self):
        try:
            res = self.ticker()
            if not res=='E':
                print('価格取得：成功')
                return float(res['ltp'])
            else:
                print('価格取得：失敗')
                return res
        except Exception as e:
            print('get_price：失敗')
            print(e)
            return 'E'

    def get_board(self):
        try:
            res = self.board()
            if not res=='E':
                print('板情報取得：成功')
                return res['asks'], res['bids']
            else:
                print('板情報取得：失敗')
                return res
        except Exception as e:
            print('get_board：失敗')
            print(e)
            return 'E'

    def get_asset(self):
        try:
            if self.product_code == 'BTC_JPY':
                res = self.asset()
                if not res=='E':
                    print('資産取得：成功')
                    jpy = float(res[0]['amount'])
                    btc = float(res[1]['amount'])
                    btc_price = self.get_price()
                    return jpy + btc*btc_price
                else:
                    print('資産取得：失敗')
                    return res
            else:  # product_code=='FX_BTC_JPY'
                res = self.asset()
                if not res=='E':
                    print('資産取得：成功')
                    asset = res['collateral']
                    pnl = res['open_position_pnl']

                    return float(asset + pnl)
                else:
                    print('資産取得：失敗')
                    return res
        except Exception as e:
            print('get_asset：失敗')
            print(e)
            return 'E'

    def get_position(self):
        try:
            if self.product_code == 'BTC_JPY':
                res = self.asset()
                if not res=='E':
                    print('資産取得：成功')
                    return int(float(res[1]['amount'])*1000)/1000
                else:
                    print('資産取得：失敗')
                    return res
            else:  # product_code=='FX_BTC_JPY'
                res = self.position()
                if not res=='E':
                    print('ポジション取得：成功')
                    posi = 0
                    for p in res:
                        if p['side'] == 'BUY':
                            posi += p['size']
                        else:
                            posi -= p['size']

                    return int(float(posi)*100)/100
                else:
                    print('ポジション取得：失敗')
                    return res
        except Exception as e:
            print('get_position：失敗')
            print(e)
            return 'E'

    def make_order(self, side, size):
        try:
            params = {'product_code': self.product_code,
                      'child_order_type': self.order_type,
                      'side': side}
            if self.order_type == 'LIMIT':
                asks, bids = self.get_board()
                if side == 'BUY':
                    price = int(float(asks[0]['price'])) - self.advantage
                else:  # side == 'SELL'
                    price = int(float(bids[0]['price'])) + self.advantage
                params['price'] = price

            if self.product_code == 'BTC_JPY' and 0.001 <= size:
                amount = int(float(size)*1000)/1000
                params['size'] = amount
                self.order(params)
            elif self.product_code == 'FX_BTC_JPY' and 0.01 <= size:
                amount = int(float(size)*100)/100
                params['size'] = amount
                self.order(params)
        except Exception as e:
            print('make_order：失敗')
            print(e)

    def zero_position(self, emergency=False):
        try:
            order_size = -self.get_position()
            if not order_size == 0:
                order_side = 'BUY' if order_size > 0 else 'SELL'
                if emergency:
                    pr_order_type = self.order_type
                    self.order_type = 'MARKET'
                    if self.product_code == 'BTC_JPY':
                        if order_side == 'SELL':
                            self.make_order(order_side, abs(order_size))
                    else:
                        self.make_order(order_side, abs(order_size))
                    self.order_type = pr_order_type
                else:
                    if self.product_code == 'BTC_JPY':
                        if order_side == 'SELL':
                            self.make_order(order_side, abs(order_size))
                    else:
                        self.make_order(order_side, abs(order_size))
        except Exception as e:
            print('zero_position：失敗')
            print(e)

    def make_position(self, act_position, calc_position):
        try:
            if calc_position == 0:
                self.zero_position()
            else:
                order_size = calc_position - act_position
                if order_size == 0:
                    pass
                else:
                    order_side = 'BUY' if order_size > 0 else 'SELL'
                    if self.product_code == 'BTC_JPY':
                        if calc_position > 0:
                            self.make_order(order_side, abs(order_size))
                        else:
                            self.zero_position()
                    else:
                        self.make_order(order_side, abs(order_size))
        except Exception as e:
            print('make_position：失敗')
            print(e)

    def cancel_all(self):
        try:
            endpoint = "/v1/me/cancelallchildorders"
            params = {'product_code': self.product_code}
            res = self.request(endpoint, params=params, method='POST')
            print(str(res)[:100] + '.....')

            return res
        except Exception as e:
            print('cancel_all：失敗')
            print(e)
