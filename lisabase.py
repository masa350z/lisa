import numpy as np
import csv


class Asset:
    def __init__(self, e_ratio):
        self.e_ratio = e_ratio
        self.asset_lis = []

    def refresh_asset(self, asset):
        try:
            self.asset_lis.append(asset)
            self.asset_lis = self.asset_lis[-60*24*3:]

            if len(self.asset_lis) >= 60*24:
                if 1 - self.asset_lis[-1]/self.asset_lis[-60*24] > self.e_ratio:
                    return True
                else:
                    return False
            else:
                return False
        except Exception as e:
            print('refresh_asset')
            print(e)
            return False


class Trader:
    def __init__(self, minute, max_len, pred_len, num, v_ss, rik, son, force=False):
        self.max_len = max_len
        self.pred_len = pred_len
        self.minute = minute
        self.price_list = []
        self.position = {'side': 0, 'count': 0, 'price': 0, 'std': 0}
        self.sort_range = []
        self.force = force

        self.params = {'max_length': max_len,
                       'predict_length': pred_len,
                       'number_of_sample': num,
                       'similar_value': v_ss,
                       'rikaku': rik,
                       'sonkiri': son}

        hist_data = []
        with open('histdata/btcjpy_{}m.csv'.format(minute)) as f:
            reader = csv.reader(f)
            for row in reader:
                hist_data.append(row[-1])
        hist_data = np.array(hist_data[1:], dtype='float32')

        temp = [np.roll(hist_data, -i, axis=0) for i in range(max_len)]
        data_x = np.stack(temp, axis=1)[:-(max_len - 1)][:-pred_len]

        mx = np.max(data_x, axis=1).reshape(len(data_x), 1)
        mn = np.min(data_x, axis=1).reshape(len(data_x), 1)
        norm = (data_x - mn) / (mx - mn)
        self.data_x = norm[:-pred_len]

        temp = [np.roll(hist_data[max_len:], -i, axis=0) for i in range(pred_len)]
        data_z = np.stack(temp, axis=1)[:-(pred_len - 1)]

        mx = np.max(data_x, axis=1).reshape(len(data_z), 1)
        mn = np.min(data_x, axis=1).reshape(len(data_z), 1)
        norm = (data_z - mn) / (mx - mn)

        self.data_z = norm[:len(self.data_x)]

        a = self.data_z[:, -1] - self.data_z[:, 0]
        b = np.max(self.data_z, axis=1) - np.min(self.data_z, axis=1)
        self.data_y = a/b

    def reset(self):
        self.price_list = []
        self.position = {'side': 0, 'count': 0, 'price': 0, 'std': 0}

    def ret_indication(self):
        price_np = np.array(self.price_list)
        mx, mn = np.max(price_np), np.min(price_np)
        norm = (price_np - mn) / (mx - mn)

        temp = np.sum(np.square(self.data_x - norm), axis=1)
        temp[np.isnan(temp)] = 0
        temp = 1 / (1 + temp)
        self.sort_range = np.argsort(temp)[::-1]

        differ = temp[self.sort_range][:self.params['number_of_sample']]
        indication = self.data_y[self.sort_range][:self.params['number_of_sample']]
        indicator = float(np.average(differ * indication))

        return indicator

    def refresh_position(self, price, count):
        try:
            if int(count/self.minute) == count/self.minute:
                if price:
                    self.price_list.append(price)
                if self.params['max_length'] <= len(self.price_list):
                    self.price_list = self.price_list[-self.params['max_length']:]

                    if not self.position['side'] == 0:
                        self.position['count'] -= 1

                        if self.position['count'] == 0:
                            self.position = {'side': 0, 'count': 0, 'price': 0, 'std': 0}
                        else:
                            rik_son = (price - self.position['price'])*self.position['side']/self.position['std']
                            if rik_son > self.params['rikaku'] or rik_son < -self.params['sonkiri']:
                                self.position = {'side': 0, 'count': 0, 'price': 0, 'std': 0}

                    if self.position['side'] == 0 or self.force:
                        indicator = self.ret_indication()
                        print(indicator)
                        if abs(indicator) > self.params['similar_value']:
                            std = np.std(np.array(self.price_list))
                            price = self.price_list[-1] if count == 0 else price
                            if indicator > 0:
                                self.position = {'side': 1, 'count': self.pred_len, 'price': price, 'std': std}
                            else:
                                self.position = {'side': -1, 'count': self.pred_len, 'price': price, 'std': std}

            print(self.position)
        except Exception as e:
            print('refresh_position')
            print(e)

    def return_similar(self):
        try:
            if not len(self.sort_range) == 0:
                mx = max(self.price_list)
                mn = min(self.price_list)
                temp_data_z = np.concatenate([self.data_x, self.data_z], axis=1)
                norm = temp_data_z[self.sort_range][:25]

                return norm*(mx-mn) + mn
            else:
                return []
        except Exception as e:
            print(e)
