from datetime import datetime
import requests
import hashlib
import json
import time
import hmac


class GMO:
    def __init__(self, leverage=False, advantage=0, order_type='MARKET', api_key=None, api_secret=None):
        self.api_url = "https://api.coin.z.com/public"
        self.api_prurl = "https://api.coin.z.com/private"
        self.leverage = leverage
        self.advantage = int(advantage)
        self.order_type = order_type
        self.api_key = api_key
        self.api_secret = api_secret

    def request(self, endpoint, method="GET", params=None, apitype='Public'):
        access_timestamp = '{0}000'.format(int(time.mktime(datetime.now().timetuple())))
        if method == 'GET':
            text = access_timestamp + method + endpoint
        else:
            text = access_timestamp + method + endpoint + json.dumps(params)
        access_sign = hmac.new(bytes(self.api_secret.encode('ascii')), bytes(text.encode('ascii')),
                               hashlib.sha256).hexdigest()
        auth_header = {
            "API-KEY": self.api_key,
            "API-TIMESTAMP": access_timestamp,
            "API-SIGN": access_sign
        }
        requests.Session().headers.update(auth_header)
        if apitype == 'Public':
            url = self.api_url + endpoint
        else:
            url = self.api_prurl + endpoint
        if method == "GET":
            response = requests.get(url, params=params, headers=auth_header)
        else:  # method == "POST":
            response = requests.post(url, data=json.dumps(params), headers=auth_header)

        content = json.loads(response.content.decode("utf-8"))

        return content

    def ticker(self):
        try:
            params = {'symbol': 'BTC_JPY'} if self.leverage else {'symbol': 'BTC'}
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
            params = {'symbol': 'BTC_JPY'} if self.leverage else {'symbol': 'BTC'}
            endpoint = "/v1/orderbooks"
            res = self.request(endpoint, params=params)
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('board')
            print(e)
            return 'E'

    def asset(self):
        try:
            endpoint = "/v1/account/assets"
            res = self.request(endpoint, apitype='Private')
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('asset')
            print(e)
            return 'E'

    def margin(self):
        try:
            endpoint = "/v1/account/margin"
            res = self.request(endpoint, apitype='Private')
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('margin')
            print(e)
            return 'E'

    def position(self):
        try:
            params = {'symbol': 'BTC_JPY'}
            endpoint = "/v1/openPositions"
            res = self.request(endpoint, params=params, apitype='Private')
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('position')
            print(e)
            return 'E'

    def order(self, params):
        try:
            endpoint = "/v1/order"
            res = self.request(endpoint, method='POST', params=params, apitype='Private')
            print(str(res)[:100] + '.....')
            return res
        except Exception as e:
            print('order')
            print(e)
            return 'E'

    def cancel(self):
        try:
            if self.leverage:
                params = {'symbol': 'BTC_JPY'}
            else:
                params = {'symbol': 'BTC'}
            endpoint = "/v1/activeOrders"
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
            if not res=='E':
                print('価格取得：成功')
                return float(res['data'][0]['last'])
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
                return res['data']['asks'], res['data']['bids']
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
                res = self.asset()
                if not res == 'E':
                    print('資産取得：成功')
                    jpy = float(res['data'][0]['amount'])
                    res = self.position()
                    if not res == 'E':
                        print('ポジション取得：成功')
                        if res['data'] == {}:
                            pnl = 0
                        else:
                            pnl = sum([float(i['lossGain']) for i in res['data']['list']])
                        return jpy + pnl
                    else:
                        print('ポジション取得：失敗')
                        return res
                else:
                    print('資産取得：失敗')
                    return res
            else:
                res = self.asset()
                if not res == 'E':
                    print('資産取得：成功')
                    jpy = float(res['data'][0]['amount'])
                    btc = float(res['data'][1]['amount'])
                    res = self.get_price()
                    if not res == 'E':
                        return jpy + btc*res
                else:
                    print('資産取得：失敗')
                    return res
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
                    if not res['data'] == {}:
                        posi = 0
                        for i in res['data']['list']:
                            if i['side'] == 'BUY':
                                posi += float(i['size'])
                            else:  # i['side'] == 'SELL'
                                posi -= float(i['size'])
                        return int(posi*100)/100
                    else:
                        return 0
                else:
                    print('ポジション取得：失敗')
                    return res
            else:
                res = self.asset()
                if not res == 'E':
                    print('資産取得：成功')
                    btc = int(float(res['data'][1]['amount'])*10000)/10000
                    return btc
                else:
                    print('資産取得：失敗')
                    return res
        except Exception as e:
            print('get_position：失敗')
            print(e)
            return 'E'

    def make_order(self, side, size):
        try:
            params = {'executionType': self.order_type,
                      'side': side}
            if self.order_type == 'LIMIT':
                asks, bids = self.get_board()
                if side == 'BUY':
                    price = int(float(asks[0]['price'])) - self.advantage
                else:  # side == 'SELL'
                    price = int(float(bids[0]['price'])) + self.advantage
                params['price'] = str(price)

            if self.leverage:
                if 0.01 <= size:
                    amount = int(float(size)*100)/100
                    params['size'] = str(amount)
                    params['symbol'] = 'BTC_JPY'
                    self.order(params)
            else:
                if 0.0001 <= size:
                    amount = int(float(size)*10000)/10000
                    params['size'] = str(amount)
                    params['symbol'] = 'BTC'
                    self.order(params)
        except Exception as e:
            print('make_order：失敗')
            print(e)

    def zero_position(self, emergency=False):
        try:
            if self.leverage:
                endpoint = '/v1/closeBulkOrder'
                posi = self.get_position()
                if not posi == 0:
                    if emergency:
                        params = {'symbol': 'BTC_JPY',
                                  'executionType': 'MARKET',
                                  'size': str(abs(posi))}
                        if posi > 0:
                            params['side'] = 'SELL'
                        else:
                            params['side'] = 'BUY'
                        res = self.request(endpoint, method='POST', params=params, apitype='Private')
                        print(str(res)[:100] + '.....')
                    else:
                        params = {'symbol': 'BTC_JPY',
                                  'executionType': self.order_type,
                                  'size': str(abs(posi))}
                        if posi > 0:
                            params['side'] = 'SELL'
                        else:
                            params['side'] = 'BUY'

                        if self.order_type == 'LIMIT':
                            asks, bids = self.get_board()
                            if params['side'] == 'BUY':
                                price = int(float(asks[0]['price'])) - self.advantage
                            else:  # side == 'SELL'
                                price = int(float(bids[0]['price'])) + self.advantage
                            params['price'] = str(price)

                        res = self.request(endpoint, method='POST', params=params, apitype='Private')
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
            endpoint = "/v1/cancelOrder"
            res = self.cancel()
            if not res == 'E':
                if not res['data'] == {}:
                    id_lis = [i['orderId'] for i in res['data']['list']]
                    for i in id_lis:
                        params = {'orderID': i}
                        res = self.request(endpoint, method='POST' ,params=params, apitype='Private')
                        print(str(res)[:100] + '.....')
        except Exception as e:
            print('cancel_all：失敗')
            print(e)
