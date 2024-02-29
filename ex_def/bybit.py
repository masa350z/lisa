import requests
import json
import time
import hmac


class ByBit:
    def __init__(self, leverage=True, advantage=0, order_type='MARKET', api_key=None, api_secret=None):
        self.api_url = "https://api.bybit.com"
        self.symbol = 'BTCUSDT'
        self.advantage = float(advantage)
        self.order_type = 'Market' if order_type == 'MARKET' else 'Limit'
        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout = 'GoodTillCancel'

    def get_signature(self, req_params):
        _val = '&'.join([str(k)+"="+str(v) for k, v in sorted(req_params.items()) if (k != 'sign') and (v is not None)])
        return str(hmac.new(bytes(self.api_secret, "utf-8"), bytes(_val, "utf-8"), digestmod="sha256").hexdigest())

    def request(self, endpoint, method="GET", params=None):
        if self.api_key and self.api_secret and params:
            access_timestamp = int(time.time()*1000)
            params['api_key'] = self.api_key
            params['timestamp'] = access_timestamp
            sign = self.get_signature(params)
            params['sign'] = sign

        try:
            url = self.api_url + endpoint
            with requests.Session() as s:
                if method == "GET":
                    response = s.get(url, params=params)
                else:  # method == "POST":
                    response = s.post(url, params=params)
            content = json.loads(response.content.decode("utf-8"))

            return content
        except requests.RequestException as e:
            print(e)
            raise e

    def ticker(self):
        try:
            params = {'symbol': self.symbol}
            endpoint = "/v2/public/tickers"
            res = self.request(endpoint, params=params)
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('ticker')
            print(e)
            return 'E'

    def board(self):
        try:
            params = {'symbol': self.symbol}
            endpoint = "/v2/public/orderBook/L2"
            res = self.request(endpoint, params=params)
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('board')
            print(e)
            return 'E'

    def asset(self):
        try:
            params = {'coin': 'USDT'}
            endpoint = "/v2/private/wallet/balance"
            res = self.request(endpoint, params=params)
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('asset')
            print(e)
            return 'E'

    def position(self):
        try:
            params = {'symbol': self.symbol}
            endpoint = "/private/linear/position/list"
            res = self.request(endpoint, params=params)
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('position')
            print(e)
            return 'E'

    def order(self, params):
        try:
            endpoint = "/private/linear/order/create"
            res = self.request(endpoint, method="POST", params=params)
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
                return float(res['result'][0]['last_price'])
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
                asks, bids = [], []
                for i in res['result']:
                    if i['side'] == 'Buy':
                        bids.append(i)
                    else:
                        asks.append(i)
                return asks, bids
            else:
                print('板情報取得：失敗')
                return res
        except Exception as e:
            print('get_board：失敗')
            print(e)
            return 'E'

    def get_asset(self):
        try:
            res = self.asset()
            if not res=='E':
                print('資産取得：成功')
                return float(res['result']['USDT']['equity'])
            else:
                print('資産取得：失敗')
                return res
        except Exception as e:
            print('get_asset：失敗')
            print(e)
            return 'E'

    def get_position(self):
        try:
            position = 0
            res = self.position()
            if not res=='E':
                print('ポジション取得：成功')
                for i in res['result']:
                    if i['side'] == 'Buy':
                        position += float(i['size'])
                    else:
                        position -= float(i['size'])

                return int(float(position)*1000)/1000
            else:
                print('ポジション取得：失敗')
                return res
        except Exception as e:
            print('get_position：失敗')
            print(e)
            return 'E'

    def make_order(self, side, size, reduce_only=False):
        try:
            params = {'symbol': self.symbol,
                      'side': 'Buy' if side == 'BUY' else 'Sell',
                      'order_type': self.order_type,
                      'reduce_only': reduce_only,
                      'time_in_force': self.timeout,
                      'close_on_trigger': False}

            if self.order_type == 'Limit':
                asks, bids = self.get_board()
                if side == 'BUY':
                    price = float(asks[0]['price']) - self.advantage
                else:  # side == 'SELL'
                    price = float(bids[0]['price']) + self.advantage
                print(price)
                params['price'] = price

            if 0.001 <= size:
                amount = int(float(size)*1000)/1000
                params['qty'] = amount
                self.order(params)
        except Exception as e:
            print('make_order：失敗')
            print(e)

    def zero_position(self, emergency=False):
        try:
            amount = self.get_position()
            if not amount == 0:
                if emergency:
                    pr_order_type = self.order_type
                    self.order_type = 'Market'
                    if amount > 0:
                        self.make_order('SELL', abs(amount), reduce_only=True)
                    else:
                        self.make_order('BUY', abs(amount), reduce_only=True)
                    self.order_type = pr_order_type
                else:
                    if amount > 0:
                        self.make_order('SELL', abs(amount), reduce_only=True)
                    else:
                        self.make_order('BUY', abs(amount), reduce_only=True)
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
                                self.make_order('BUY', abs(order_size), reduce_only=True)
                        else:
                            if act_position <= 0:
                                self.make_order('SELL', abs(order_size))
                            else:
                                self.make_order('SELL', abs(order_size), reduce_only=True)

        except Exception as e:
            print('make_position：失敗')
            print(e)

    def cancel_all(self):
        try:
            params = {'symbol': self.symbol}
            endpoint = "/private/linear/order/cancel-all"
            res = self.request(endpoint, method='POST', params=params)
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('cancel_all：失敗')
            print(e)
