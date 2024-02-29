import urllib.parse
import requests
import json
import time
import jwt


class Liquid:
    def __init__(self, leverage=False, advantage=0, order_type='MARKET', api_key=None, api_secret=None):
        self.api_url = "https://api.liquid.com"
        self.leverage = leverage
        self.advantage = int(advantage)
        self.order_type = order_type
        self.api_key = api_key
        self.api_secret = api_secret

    def request(self, endpoint, method="GET", params=None):
        if method == 'GET':
            if params:
                endpoint += "?" + urllib.parse.urlencode(params)
        auth_header = None

        if self.api_key and self.api_secret:
            timestamp = str(int(time.time() * 1000))
            payload = {
                "path": endpoint,
                "nonce": timestamp,
                "token_id": self.api_key
            }
            signature = jwt.encode(payload, self.api_secret, algorithm='HS256')
            auth_header = {
                'X-Quoine-API-Version': '2',
                'X-Quoine-Auth': signature,
                'Content-Type': 'application/json'
            }
        try:
            with requests.Session() as s:
                if auth_header:
                    s.headers.update(auth_header)
                url = self.api_url + endpoint
                if method == "GET":
                    response = s.get(url, params=params)
                elif method == "DELETE":
                    response = s.delete(url, params=params)
                elif method == "PUT":
                    response = s.put(url, data=json.dumps(params))
                else:  # method == "POST":
                    response = s.post(url, data=json.dumps(params))
            content = json.loads(response.content.decode("utf-8"))

            return content
        except requests.RequestException as e:
            print(e)
            raise e

    def ticker(self):
        try:
            params = {'id': '5'}
            endpoint = "/products/{}/".format(params['id'])
            res = self.request(endpoint, params=params)
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('ticker')
            print(e)
            return 'E'

    def board(self):
        try:
            params = {'id': '5'}
            endpoint = "/products/{}/price_levels".format(params['id'])
            res = self.request(endpoint, params=params)
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('board')
            print(e)
            return 'E'

    def asset(self):
        try:
            endpoint = "/accounts/balance"
            res = self.request(endpoint, params=None)
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('asset')
            print(e)
            return 'E'

    def position(self):
        try:
            endpoint = "/trades"
            res = self.request(endpoint, params=None)
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('position')
            print(e)
            return 'E'

    def order(self, params):
        try:
            endpoint = "/orders/"
            res = self.request(endpoint, method='POST', params=params)
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('order')
            print(e)
            return 'E'

    def cancel(self):
        try:
            endpoint = "/orders"
            res = self.request(endpoint, params=None)
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('position')
            print(e)
            return 'E'

    def get_price(self):
        try:
            res = self.ticker()
            if not res=='E':
                print('価格取得：成功')
                return float(res['market_ask'])
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
                return res['sell_price_levels'], res['buy_price_levels']
            else:
                print('板情報取得：失敗')
                return res
        except Exception as e:
            print('get_board：失敗')
            print(e)
            return 'E'

    def get_asset(self):
        try:
            if self.leverage:
                asset = 0
                res = self.position()
                if not res=='E':
                    print('ポジション取得：成功')
                    for i in res['models']:
                        if not float(i['open_quantity']) == 0:
                            asset += +float(i['pnl'])
                    res = self.asset()
                    if not res=='E':
                        print('資産取得：成功')
                        asset += float(res[0]['balance'])
                        return asset
                    else:
                        print('資産取得：失敗')
                        return res
                else:
                    print('ポジション取得：失敗')
                    return res
            else:
                asset = 0
                price = self.get_price()
                if not price == 'E':
                    res = self.asset()
                    if not res == 'E':
                        print('資産取得：成功')
                        btc = float(res[1]['balance'])
                        asset += btc*price
                        asset += float(res[0]['balance'])
                        return asset
                    else:
                        print('資産取得：失敗')
                        return res
                else:
                    return price

        except Exception as e:
            print('get_asset：失敗')
            print(e)
            return 'E'

    def get_position(self):
        try:
            if self.leverage:
                res = self.position()
                if not res == 'E':
                    print('ポジション取得：成功')
                    posi = 0
                    for i in res['models']:
                        if not float(i['open_quantity']) == 0:
                            if i['side'] == 'long':
                                posi += float(i['quantity'])
                            else:
                                posi -= float(i['quantity'])
                    return posi
                else:
                    print('ポジション取得：失敗')
                    return res
            else:
                res = self.asset()
                if not res == 'E':
                    print('資産取得：成功')
                    btc = int(float(res[1]['balance'])*1000)/1000
                    return btc
                else:
                    print('資産取得：失敗')
                    return res
        except Exception as e:
            print('get_position：失敗')
            print(e)
            return 'E'

    def make_order(self, side, size):
        inp_side = 'buy' if side == 'BUY' else 'sell'
        inp_type = 'market' if self.order_type == 'MARKET' else 'limit'
        try:
            if 0.001 <= size:
                params = {'order_type': inp_type,
                          'product_id': 5,
                          'side': inp_side}
                if self.leverage:
                    params['leverage_level'] = 4

                if inp_type == 'limit':
                    asks, bids = self.get_board()
                    if side == 'BUY':
                        price = int(float(asks[0][0])) - self.advantage
                    else:  # side == 'SELL'
                        price = int(float(bids[0][0])) + self.advantage
                    params['price'] = price
                amount = int(float(size)*1000)/1000
                params['quantity'] = amount
                self.order(params)
        except Exception as e:
            print('make_order：失敗')
            print(e)

    def zero_position(self, emergency=False):
        try:
            if self.leverage:
                endpoint = '/trades/close_all'
                res = self.request(endpoint, method='PUT', params=None)
                print(str(res)[:100] + '.....')
            else:
                amount = self.get_position()
                if emergency:
                    pr_order_type = self.order_type
                    self.order_type = 'MARKET'
                    self.make_order('SELL', amount)
                    self.order_type = pr_order_type
                else:
                    self.make_order('SELL', amount)
        except Exception as e:
            print('zero_position：失敗')
            print(e)

    def make_position(self, act_position, calc_position):
        try:
            if calc_position == 0:
                self.zero_position()
            else:
                order_size = calc_position - act_position
                if not order_size == 0:
                    if self.leverage:
                        if calc_position * act_position < 0:
                            self.zero_position()
                            if order_size > 0:
                                self.make_order('BUY', abs(calc_position))
                            else:
                                self.make_order('SELL', abs(calc_position))
                        else:
                            if order_size > 0:
                                if act_position >= 0:
                                    self.make_order('BUY', abs(order_size))
                                else:
                                    self.zero_position()
                                    self.make_order('SELL', abs(calc_position))
                            else:
                                if act_position <= 0:
                                    self.make_order('SELL', abs(order_size))
                                else:
                                    self.zero_position()
                                    self.make_order('BUY', abs(calc_position))
                    else:
                        if calc_position > 0:
                            if order_size > 0:
                                self.make_order('BUY', abs(order_size))
                            else:  # order_size < 0
                                self.make_order('SELL', abs(order_size))
                        else:
                            self.zero_position()
        except Exception as e:
            print('make_position：失敗')
            print(e)

    def cancel_all(self):
        try:
            res = self.cancel()
            if not res == 'E':
                id_lis = []
                for i in res['models']:
                    if i['status'] == 'live' and i['product_id'] == 5:
                        id_lis.append(i['id'])
                if not len(id_lis) == 0:
                    for i in id_lis:
                        params = {'id': i}
                        endpoint = "/orders/{}/cancel".format(i)
                        res = self.request(endpoint, params=params, method='PUT')
                        print(str(res)[:100] + '.....')
        except Exception as e:
            print('cancel_all：失敗')
            print(e)
