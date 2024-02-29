import urllib.parse
import requests
import hashlib
import json
import time
import hmac


class BitBank:
    def __init__(self, leverage=False, advantage=0, order_type='MARKET', api_key=None, api_secret=None):
        self.api_url = "https://public.bitbank.cc"
        self.api_prurl = "https://api.bitbank.cc/v1"
        self.advantage = int(advantage)
        self.order_type = order_type
        self.api_key = api_key
        self.api_secret = api_secret

    def request(self, endpoint, method="GET", params=None, apitype='Public'):
        body = ""
        if method == "POST":
            body = json.dumps(params)
        else:
            if params:
                body = "?" + urllib.parse.urlencode(params)

        auth_header = None
        if self.api_key and self.api_secret:
            access_timestamp = str(int(time.time() * 1000))
            api_secret = str.encode(self.api_secret)
            if method == 'POST':
                text = str.encode(access_timestamp + body)
            else:
                text = str.encode(access_timestamp + ('/v1' + endpoint) + body)
            access_sign = hmac.new(api_secret,
                                   text,
                                   hashlib.sha256).hexdigest()
            auth_header = {
                "ACCESS-KEY": self.api_key,
                "ACCESS-NONCE": access_timestamp,
                "ACCESS-SIGNATURE": access_sign,
                "Content-Type": "application/json"
            }

        try:
            with requests.Session() as s:
                if auth_header:
                    s.headers.update(auth_header)

                if apitype == 'Public':
                    url = self.api_url + endpoint
                else:
                    url = self.api_prurl + endpoint

                if method == "GET":
                    response = s.get(url, params=params)
                elif method == "DELETE":
                    response = s.delete(url, params=params)
                else:  # method == "POST":
                    response = s.post(url, data=json.dumps(params))
            content = json.loads(response.content.decode("utf-8"))

            return content
        except requests.RequestException as e:
            print(e)
            raise e

    def ticker(self):
        try:
            params = {'pair': 'btc_jpy'}
            endpoint = "/{}/ticker".format(params['pair'])
            res = self.request(endpoint, params=params)

            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('ticker')
            print(e)
            return 'E'

    def board(self):
        try:
            params = {'pair': 'btc_jpy'}
            endpoint = "/{}/depth".format(params['pair'])
            res = self.request(endpoint, params=params)
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('board')
            print(e)
            return 'E'

    def asset(self):
        try:
            endpoint = "/user/assets"
            res = self.request(endpoint, apitype='Private')
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('asset')
            print(e)
            return 'E'

    def order(self, params):
        try:
            endpoint = "/user/spot/order"
            res = self.request(endpoint, 'POST', params=params, apitype='Private')
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('order')
            print(e)
            return 'E'

    def cancel(self):
        try:
            params = {'pair': 'btc_jpy'}
            endpoint = "/user/spot/active_orders"
            res = self.request(endpoint, params=params, apitype='Private')
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('cancel')
            print(e)
            return 'E'

    def get_price(self):
        try:
            res = self.ticker()
            if not res == 'E':
                print('価格取得：成功')
                return float(res['data']['last'])
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
            if not res == 'E':
                print('板情報取得：成功')
                return res['data']['asks'], res['data']['bids']
            else:
                print('板情報取得：失敗')
                return res
        except Exception as e:
            print('get_board：失敗')
            print(e)
            return False

    def get_asset(self):
        try:
            res = self.asset()
            if not res == 'E':
                print('資産取得：成功')
                jpy = float(res['data']['assets'][0]['free_amount'])
                btc = float(res['data']['assets'][1]['free_amount'])
                asset = jpy + btc * self.get_price()
                return asset
            else:
                print('資産取得：失敗')
                return res
        except Exception as e:
            print('get_asset：失敗')
            print(e)
            return False

    def get_position(self):
        try:
            res = self.asset()
            if not res == 'E':
                print('資産取得：成功')
                btc = int(float(res['data']['assets'][1]['free_amount'])*10000)/10000
                return btc
            else:
                print('資産取得：失敗')
                return res
        except Exception as e:
            print('get_position：失敗')
            print(e)
            return False

    def make_order(self, side, size):
        inp_side = 'buy' if side == 'BUY' else 'sell'
        inp_type = 'market' if self.order_type == 'MARKET' else 'limit'
        asks, bids = self.get_board()
        if side == 'BUY':
            price = int(float(asks[0][0])) - self.advantage
        else:  # side == 'SELL'
            price = int(float(bids[0][0])) + self.advantage
        try:
            if 0.0001 <= size:
                params = {'pair': 'btc_jpy',
                          'type': inp_type,
                          'side': inp_side}
                if self.order_type == 'LIMIT':
                    params['price'] = str(price)
                amount = int(float(size)*10000)/10000
                params['amount'] = amount
                self.order(params)
        except Exception as e:
            print('make_order：失敗')
            print(e)

    def zero_position(self, emergency=False):
        try:
            amount = self.get_position()
            if emergency:
                pr_order_type = self.order_type
                self.order_type = 'MARKET'
                self.make_order(side='SELL', size=abs(amount))
                self.order_type = pr_order_type
            else:
                self.make_order(side='SELL', size=abs(amount))
        except Exception as e:
            print('zero_position：失敗')
            print(e)

    def make_position(self, act_position, calc_position):
        try:
            if calc_position >= 0:
                if calc_position == 0:
                    self.zero_position()
                else:
                    order_size = calc_position - act_position
                    if order_size > 0:
                        self.make_order('BUY', abs(order_size))
                    else:
                        self.make_order('SELL', abs(order_size))
            else:
                self.zero_position()
        except Exception as e:
            print('make_position：失敗')
            print(e)
            return False

    def cancel_all(self):
        try:
            endpoint = "/user/spot/cancel_order"
            res = self.cancel()
            if not res == 'E':
                id_lis = []
                for i in res['data']['orders']:
                    id_lis.append(i['order_id'])
                if not len(id_lis) == 0:
                    for i in id_lis:
                        params = {'pair': 'btc_jpy',
                                  'order_id': i}
                        res = self.request(endpoint, params=params, method='POST', apitype='Private')
                        print(str(res)[:100] + '.....')
        except Exception as e:
            print('cancel_all：失敗')
            print(e)
