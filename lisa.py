import lisabase as lisa
import pandas as pd
import webbrowser
import requests

from ex_def import bitbankcc
from ex_def import bitflyer
from ex_def import liquid
from ex_def import bybit
from ex_def import gmo

from kivy.core.text import LabelBase, DEFAULT_FONT
from kivy.resources import resource_add_path
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.app import App

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.uix.switch import Switch
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.image import Image

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('module://kivy.garden.matplotlib.backend_kivy')

Window.size = (int(1920*0.6), int(1080*0.7))
Window.color = (100, 100, 100, 100)

resource_add_path('./fonts')
LabelBase.register(DEFAULT_FONT, 'mplus-2c-regular.ttf')

Button.background_disabled_normal = 'pics/button_gray.png'
Button.background_disabled_down = 'pics/button_gray.png'
Button.background_down = 'pics/button_gray.png'

white_button = 'pics/button_white.png'
green_button = 'pics/button_green.png'
red_button = 'pics/button_red.png'

key = 'NplYhrxj9j9tBp5indFESa0w4DdAe42l203MxkGI'
get_price_url = 'https://l73uak3tug.execute-api.ap-northeast-1.amazonaws.com/stage1/hist/exchangeexchange'
register_payments_url = 'https://rkkn74zms5.execute-api.ap-northeast-1.amazonaws.com/stage1/payments/numbernumber/priceprice/addressaddress'
params_dir = 'docs/settings.csv'
number_dir = 'docs/number.csv'
qty_dir = 'docs/qty.csv'
qty_dic = {'free': 0.04,
           'oteErJB8YqSLDt8zhSIJpvE0pfAzQNfwdm1fFCDE8PJ5g0Z3UUk3kNg5fH9vz1sFg0R2zE1sW2BANooMmGHLwaTBf2yi346bohKX': 0.08,
           'xNJTo5795SAfOv6CooNZzqQWxnNFp8Ns9DKAiY8DL0zFrrBl2vWZTdNViDDVjyAunawO4ZAKxCT1VrOkHUZbtNYKlCFTAozuuwae': 0.4,
           '8V50Z51pY7r8xGOJ5b8IIFAkgUw8fFcTlVDwargJblEAQRoedisdCn3vk2MRVHkuRrb4zVgC2w6E47AxwkHKRJRm5avQXtidrmsu': 1,
           'uQhgU171nXDMbHVjcukJLvL4KYB0MK0yTgU3oBm3dbWIhj1BGVqgFDz64KktpwRMyXaquAx1fNxTmBH9ETdOnG53DT3FAM3ixYV5': 1000000}


def plot_data(price_list, similar):
    fig = plt.figure(facecolor='#090909')
    ax = fig.add_subplot(1, 1, 1)
    ax.set_facecolor('#090909')
    ax.grid(linewidth=0.1, color='darkslategrey', alpha=0.4)
    for i in ['left', 'bottom']:
        ax.spines[i].set_color('white')
    for i in ['right', 'top']:
        ax.spines[i].set_color('#090909')
    ax.tick_params(labelbottom=False,
                   labeltop=False,
                   color='white')
    ax.tick_params(axis='y', colors='white')

    if not similar is None:
        for i in similar:
            ax.plot(range(len(i)), i, alpha=0.5)
        ax.plot(range(len(price_list)), price_list, color='white')
    else:
        y = price_list[-60 * 24:]
        x = range(len(y))
        ax.plot(x, y, color='white')
    plt.close()

    return fig.canvas

def make_exobject(dataframe):
    api = str(dataframe['api_key'][0])
    sct = str(dataframe['secret_key'][0])
    order = dataframe['order'][0]
    advantage = dataframe['advantage'][0]
    lev = True if dataframe['leverage'][0] == 1 else False
    exchange = dataframe['exchange'][0]

    if exchange == 'bitflyer':
        ex = bitflyer.BitFlyer(lev, advantage, order, api, sct)
    elif exchange == 'bitbankcc':
        ex = bitbankcc.BitBank(lev, advantage, order, api, sct)
    elif exchange == 'liquid':
        ex = liquid.Liquid(lev, advantage, order, api, sct)
    elif exchange == 'bybit':
        ex = bybit.ByBit(lev, advantage, order, api, sct)
    else:
        ex = gmo.GMO(lev, advantage, order, api, sct)

    return ex

def register_qty(amount):
    for i in qty_dic.keys():
        if qty_dic[i] == amount:
            pd.DataFrame([{'qty': i}]).to_csv(qty_dir, index=False, encoding='utf_8_sig')
            break


class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.clear_widgets()
        dataframe = pd.read_csv(params_dir)

        self.count, self.emergency = 0, False
        self.order = dataframe['order'][0]
        self.api_key = str(dataframe['api_key'][0])
        self.sct_key = str(dataframe['secret_key'][0])
        self.lev = True if dataframe['leverage'][0] == 1 else False
        self.exchange = dataframe['exchange'][0]
        self.e_ratio = dataframe['emergency'][0]
        self.ex = make_exobject(dataframe)
        self.asset_obj = lisa.Asset(e_ratio=self.e_ratio)
        self.data_list = [lisa.Trader(1, 90, 30, 1000, 0.06, 2, 2, force=True),
                          lisa.Trader(1, 90, 60, 1000, 0.07, 8, 1),
                          lisa.Trader(1, 60, 30, 1000, 0.09, 100, 6),
                          lisa.Trader(1, 60, 60, 500, 0.09, 2, 1.5)]

        qty_num = pd.read_csv(qty_dir)['qty'][0]
        self.max_qty = qty_dic[qty_num]/len(self.data_list)
        self.amount = dataframe['amount'][0] if dataframe['amount'][0] < self.max_qty else self.max_qty

        self.is_countdown = False
        self.panels = BoxLayout(orientation='vertical', size_hint_x=1, padding=(20, 20))
        self.panels.add_widget(Label(text="LISA", font_size=64, size_hint_y=1))

        self.exchange_ = Label(text=self.exchange)
        self.leverage = Label(text='レバレッジ' if self.lev else '現物')
        self.market = Label(text='指値' if self.order == 'LIMIT' else '成行')
        self.amount_v = Label(text='{} BTC'.format(self.amount))
        self.status = Label(text='停止中')
        self.position = Label(text='+0.0 BTC')
        self.asset = Label(text='---')
        self.base_currency = '＄' if self.exchange == 'bybit' else '￥'

        self.info = self.return_info()
        self.panels.add_widget(self.info)

        self.btn1 = Button(text='設定', font_size=32, on_press=self.go_setting)
        self.btn2 = Button(text='アップグレード', font_size=16, on_press=self.upgrade_pop)
        for i in [self.btn1, self.btn2]:
            i.background_normal = white_button

        self.start_btn = Button(text='起動', font_size=38, on_press=self.start, background_normal=green_button)
        self.stop_btn = Button(text='停止', font_size=38, on_press=self.stop, background_normal=red_button)
        self.stop_btn.disabled = True

        self.control = self.return_control()
        self.panels.add_widget(self.control)
        self.upgrade_bx = BoxLayout(padding=(10, 10), size_hint_y=0.5)
        self.upgrade_bx.add_widget(self.btn2)
        self.panels.add_widget(self.upgrade_bx)
        self.add_widget(self.panels)

        self.graph = plot_data([], None)
        self.graph.size_hint_y = 2.7

        self.asset_graph = plot_data([], None)
        self.asset_graph.size_hint_y = 1

        self.graph_box = BoxLayout(orientation='vertical', size_hint_x=2.5, padding=(25, 25), spacing=25)
        self.graph_box.add_widget(self.graph)
        self.graph_box.add_widget(self.asset_graph)
        self.add_widget(self.graph_box)

    def return_info(self):
        items = BoxLayout(orientation='vertical')
        for i in ['取引所', '取引タイプ', '注文タイプ', '最小取引量', '状態', '保有数', '資産']:
            items.add_widget(Label(text=i, font_size=18))
        values = BoxLayout(orientation='vertical')
        for i in [self.exchange_, self.leverage, self.market, self.amount_v, self.status, self.position, self.asset]:
            i.font_size = 18
            values.add_widget(i)
        info = BoxLayout(size_hint_y=2.5)
        for i in [items, values]:
            info.add_widget(i)

        return info

    def return_control(self):
        btn = BoxLayout(orientation='vertical', spacing=10)
        for i in [self.btn1]:
            btn.add_widget(i)

        launch = BoxLayout(orientation='vertical', spacing=10)
        for i in [self.start_btn, self.stop_btn]:
            launch.add_widget(i)

        control = BoxLayout(spacing=20, size_hint_y=3, padding=(10, 10))
        for i in [btn, launch]:
            control.add_widget(i)

        return control

    def run_system(self, *args):
        try:
            self.ex.cancel_all()
            self.status.text = '動作中'
            if not self.emergency:
                self.count += 1
                asset = self.ex.get_asset()

                if not asset == 'E':
                    self.asset.text = '{} {}'.format(str("{:,}".format(int(asset))), self.base_currency)

                    if not self.asset_obj.refresh_asset(float(asset)):
                        price = self.ex.get_price()

                        if not price == 'E':
                            for i in self.data_list:
                                i.refresh_position(price, self.count)
                            calc_position = round(sum([i.position['side'] for i in self.data_list]) * self.amount, 4)
                            act_position = self.ex.get_position()
                            if calc_position >= 0:
                                show_position = '+{}'.format(abs(calc_position))
                            else:
                                if self.lev:
                                    show_position = '-{}'.format(abs(calc_position))
                                else:
                                    show_position = '+0.0'
                            self.position.text = '{} BTC'.format(show_position)

                            if not act_position == 'E':
                                self.ex.make_position(act_position, calc_position)
                        else:
                            self.status.text = 'エラー002'
                    else:
                        self.status.text = '緊急停止'
                        self.ex.zero_position(emergency=True)
                        self.emergency = True
                else:
                    self.status.text = 'エラー001'

                similar = self.data_list[0].return_similar()

                self.graph_box.remove_widget(self.graph)
                if not len(similar) == 0:
                    self.graph = plot_data(self.data_list[0].price_list, similar)
                else:
                    self.graph = plot_data(self.data_list[0].price_list, None)

                self.graph.size_hint_y = 2.7
                self.graph_box.add_widget(self.graph)
                self.graph_box.remove_widget(self.asset_graph)
                self.asset_graph = plot_data(self.asset_obj.asset_lis, None)
                self.asset_graph.size_hint_y = 1
                self.graph_box.add_widget(self.asset_graph)
            else:
                self.status.text = '緊急停止'
                self.ex.zero_position(emergency=True)
        except Exception as e:
            print(e)
            self.status.text = 'エラー000'

    def start(self, *args):
        if not self.is_countdown:
            self.status.text = '動作中'
            self.count = 0
            self.is_countdown = True
            self.stop_btn.disabled = False
            self.start_btn.disabled = True
            self.btn1.disabled = True
            # self.btn2.disabled = True
            self.asset.text = '---'
            self.ex.cancel_all()
            self.ex.zero_position(emergency=True)
            asset = self.ex.get_asset()
            if not asset == 'E':
                self.asset.text = '{} {}'.format(str("{:,}".format(int(asset))), self.base_currency)
                self.asset_obj.asset_lis.append(int(asset))
                self.position.text = '+0.0 BTC'
            else:
                self.status.text = 'エラー011'
            try:
                ex_code = 'bitflyer-fx' if self.exchange == 'bitflyer' and self.lev else self.exchange
                ex_params = {'exchange': ex_code}
                res = requests.get(get_price_url, params=ex_params)
                print(str(res.json())[:100] + '.....')
                price_list = res.json()['data']
                for i in self.data_list:
                    minute = i.minute
                    i.price_list = price_list[::-1][::minute][::-1][-i.max_len:]
                    i.refresh_position(None, self.count)
                calc_position = round(sum([i.position['side'] for i in self.data_list]) * self.amount, 4)
                act_position = self.ex.get_position()
                if calc_position >= 0:
                    show_position = '+{}'.format(abs(calc_position))
                else:
                    if self.lev:
                        show_position = '-{}'.format(abs(calc_position))
                    else:
                        show_position = '+0.0'
                self.position.text = '{} BTC'.format(show_position)

                if not act_position == 'E':
                    self.ex.make_position(act_position, calc_position)
            except Exception as e:
                print(e)
            try:
                similar = self.data_list[0].return_similar()
                self.graph_box.remove_widget(self.graph)
                if not len(similar) == 0:
                    self.graph = plot_data(self.data_list[0].price_list, similar)
                else:
                    self.graph = plot_data(self.data_list[0].price_list, None)
                self.graph.size_hint_y = 2.7
                self.graph_box.add_widget(self.graph)
                self.graph_box.remove_widget(self.asset_graph)
                self.asset_graph = plot_data(self.asset_obj.asset_lis, None)
                self.asset_graph.size_hint_y = 1
                self.graph_box.add_widget(self.asset_graph)

            except Exception as e:
                print(e)
                self.status.text = 'エラー010'
            Clock.schedule_interval(self.run_system, 60.0)

    def stop(self, *args):
        self.status.text = '停止中'
        self.position.text = '+0.0 BTC'
        self.is_countdown = False
        self.start_btn.disabled = False
        self.stop_btn.disabled = True
        self.btn1.disabled = False
        self.btn2.disabled = False
        Clock.unschedule(self.run_system)

        self.count = 0
        self.emergency = False
        self.asset_obj.__init__(self.e_ratio)
        for i in self.data_list:
            i.reset()
        self.ex.zero_position(emergency=True)

    def go_setting(self, *args):
        self.stop_btn.disabled = True
        self.start_btn.disabled = True
        self.btn1.disabled = True
        self.btn2.disabled = True
        self.setting = BoxLayout(size_hint_x=2.5, orientation='vertical')
        title = Label(text='取引設定', font_size=36)

        items = BoxLayout(orientation='vertical', )
        for i in ['取引所', '注文方法', 'レバレッジ', '最小取引量(BTC)', '最大取引量(BTC)', '緊急停止(%)']:
            lb = Label(text=i, font_size=18)
            items.add_widget(lb)

        values = BoxLayout(orientation='vertical', padding=(50, 0), size_hint_x=1.4)

        exchange_bx = BoxLayout(spacing=10)
        self.exchange_st = Spinner(text=self.exchange, values=('bitflyer', 'bitbankcc', 'liquid', 'GMO', 'bybit'))
        self.api_st = Button(text='APIキー入力/確認', on_press=self.popup_open)
        exchange_bx.add_widget(self.exchange_st)
        exchange_bx.add_widget(self.api_st)
        values.add_widget(exchange_bx)

        order_bx = BoxLayout(padding=(0, 10))
        self.order_st = Spinner(text='指値' if self.order == 'LIMIT' else '成行', values=('成行', '指値'))
        order_bx.add_widget(self.order_st)
        values.add_widget(order_bx)

        leverage_bx = BoxLayout()
        self.leverage_st = Switch(active=self.lev)
        leverage_bx.add_widget(self.leverage_st)
        values.add_widget(leverage_bx)

        mn_bx = BoxLayout(padding=(0, 20))
        self.mn_st = TextInput(text=str(self.amount), multiline=False,	input_filter='float', on_text_validate=self.ret_max)
        self.mn_st.text_size = self.mn_st.size
        self.mn_st.halign = 'center'
        self.mn_st.valign = 'middle'
        plus01 = Button(text='+0.1', on_press=self.plus_value01)
        plus001 = Button(text='+0.01', on_press=self.plus_value001)
        plus0001 = Button(text='+0.001', on_press=self.plus_value0001)
        clear = Button(text='リセット', on_press=self.clear_value)

        mn_bx.add_widget(self.mn_st)
        for i in [plus01, plus001, plus0001, clear]:
            mn_bx.add_widget(i)
        values.add_widget(mn_bx)

        mx_box = BoxLayout()
        self.mx_st = Label(text=str(self.amount*len(self.data_list)))
        mx_box.add_widget(self.mx_st)
        values.add_widget(mx_box)

        sld_bx = BoxLayout()
        sld = BoxLayout()
        self.SampleSlider1 = Slider(min=0, max=100, value=int(self.e_ratio*100), size_hint_x=3)
        self.SampleSlider1.bind(value=self.SampleSlider1callback)
        self.Slider1Value = Label(text="100")
        self.Slider1Value.text = str(int(self.SampleSlider1.value))
        sld.add_widget(self.SampleSlider1)
        sld.add_widget(self.Slider1Value)
        sld_bx.add_widget(sld)
        values.add_widget(sld_bx)

        main = BoxLayout(size_hint_y=5, padding=(0, 20))
        main.add_widget(items)
        main.add_widget(values)

        self.message = Label(text='', size_hint_y=0.2)

        back_box = BoxLayout(padding=(250, 20), orientation='vertical', size_hint_y=1.5, spacing=10)
        back_box.add_widget(Button(text='保存', on_press=self.save_settings))
        back_box.add_widget(Button(text='戻る', on_press=self.setting_home, background_normal=white_button))

        self.setting.add_widget(title)
        self.setting.add_widget(main)
        self.setting.add_widget(self.message)
        self.setting.add_widget(back_box)

        self.remove_widget(self.graph_box)
        self.add_widget(self.setting)

    def ret_max(self, *args):
        self.mx_st.text = str(round(float(self.mn_st.text)*len(self.data_list), 3))

    def plus_value01(self, *args):
        self.mn_st.text = str(round(float(self.mn_st.text) + 0.1, 3))
        self.ret_max()

    def plus_value001(self, *args):
        self.mn_st.text = str(round(float(self.mn_st.text) + 0.01, 3))
        self.ret_max()

    def plus_value0001(self, *args):
        self.mn_st.text = str(round(float(self.mn_st.text) + 0.001, 3))
        self.ret_max()

    def clear_value(self, *args):
        self.mn_st.text = '0.0'
        self.ret_max()

    def SampleSlider1callback(self, *args):
        self.Slider1Value.text = str(int(self.SampleSlider1.value))

    def popup_open(self, *args):
        self.popup = Popup(title='API/シークレットキー入力', size_hint=(0.8, 0.8))
        popup_bx = BoxLayout(orientation='vertical')

        api_bx = BoxLayout(orientation='vertical', padding=(50, 20))
        api_bx.add_widget(Label(text='APIキー'))
        self.api_tx = TextInput(hint_text='APIキーを入力', multiline=False)
        api_bx.add_widget(self.api_tx)
        popup_bx.add_widget(api_bx)

        sct_bx = BoxLayout(orientation='vertical', padding=(50, 20))
        sct_bx.add_widget(Label(text='シークレットキー'))
        self.sct_tx = TextInput(hint_text='シークレットキーを入力', multiline=False)
        sct_bx.add_widget(self.sct_tx)
        popup_bx.add_widget(sct_bx)

        self.message_api = Label(text='', size_hint_y=0.1)
        popup_bx.add_widget(self.message_api)

        bt_bx = BoxLayout(orientation='vertical', padding=(180, 20))
        bt_bx.add_widget(Button(text='API/シークレットキーの確認', on_press=self.confirm_key))
        button_bx = BoxLayout(size_hint_y=1.3)
        cancel = Button(text='戻る', on_press=self.popup_close)
        save = Button(text='保存', on_press=self.save_api)
        button_bx.add_widget(cancel)
        button_bx.add_widget(save)
        bt_bx.add_widget(button_bx)
        popup_bx.add_widget(bt_bx)

        self.popup.content = popup_bx
        self.popup.open()

    def popup_close(self, *args):
        self.popup.dismiss()

    def confirm_key(self, *args):
        self.confirm = Popup(title='API/シークレットキー確認', size_hint=(0.8, 0.8))
        popup_bx = BoxLayout(orientation='vertical')

        api_bx = BoxLayout(orientation='vertical', padding=(50, 20))
        api_bx.add_widget(Label(text='APIキー'))
        api_tx = Label(text=self.api_key)
        api_bx.add_widget(api_tx)
        popup_bx.add_widget(api_bx)

        sct_bx = BoxLayout(orientation='vertical', padding=(50, 20))
        sct_bx.add_widget(Label(text='シークレットキー'))
        sct_tx = Label(text=self.sct_key)
        sct_bx.add_widget(sct_tx)
        popup_bx.add_widget(sct_bx)

        button_bx = BoxLayout(padding=(180, 50), size_hint_y=1.3)
        cancel = Button(text='戻る', on_press=self.dismiss_key)
        button_bx.add_widget(cancel)
        popup_bx.add_widget(button_bx)

        self.confirm.content = popup_bx
        self.confirm.open()

    def dismiss_key(self, *args):
        self.confirm.dismiss()

    def setting_home(self, *args):
        self.start_btn.disabled = False
        self.btn1.disabled = False
        self.btn2.disabled = False
        self.remove_widget(self.setting)
        self.add_widget(self.graph_box)

    def save_api(self, *args):
        if str(self.api_tx.text) == '':
            message = 'APIキーを入力してください'
        else:
            self.api_key = str(self.api_tx.text)
            if str(self.sct_tx.text) == '':
                message = 'シークレットキーを入力してください'
            else:
                self.sct_key = str(self.sct_tx.text)
                message = '保存しました'

        self.message_api.text = message
        self.make_dataframe()

    def save_settings(self, *args):
        if self.exchange_st.text == '取引所を選択':
            message = '取引所を選択してください'
        else:
            self.exchange = self.exchange_st.text
            if self.order_st.text == '成行/指値':
                message = '注文方法を選択してください'
            else:
                self.order = 'LIMIT' if self.order_st.text == '指値' else 'MARKET'
                self.lev = self.leverage_st.active
                if self.mn_st.text == '':
                    message = '最小取引量を入力してください'
                else:
                    self.amount = round(float(self.mn_st.text), 4) if float(self.mn_st.text) < self.max_qty else self.max_qty
                    self.e_ratio = int(self.Slider1Value.text)/100

                    self.exchange_.text = self.exchange
                    self.base_currency = '＄' if self.exchange == 'bybit' else '￥'
                    self.market.text = '指値' if self.order == 'LIMIT' else '成行'
                    self.leverage.text = 'レバレッジ' if self.lev else '現物'
                    self.amount_v.text = '{} BTC'.format(self.amount)

                    message = '保存しました'
                    self.make_dataframe()

        dataframe = pd.read_csv(params_dir)
        self.order = dataframe['order'][0]
        self.api_key = str(dataframe['api_key'][0])
        self.sct_key = str(dataframe['secret_key'][0])
        self.lev = True if dataframe['leverage'][0] == 1 else False
        self.exchange = dataframe['exchange'][0]
        self.amount = dataframe['amount'][0]
        self.e_ratio = dataframe['emergency'][0]
        self.ex = make_exobject(dataframe)

        self.message.text = message

    def make_dataframe(self, *args):
        dataframe = {'exchange': self.exchange,
                     'api_key': self.api_key,
                     'secret_key': self.sct_key,
                     'leverage': 1 if self.lev else 0,
                     'order': self.order,
                     'advantage': 0,
                     'amount': self.amount,
                     'emergency': self.e_ratio}

        pd.DataFrame([dataframe]).to_csv(params_dir, index=False, encoding='utf_8_sig')

    def upgrade_pop(self, *args):
        self.up_pop = Popup(title='アップグレード', size_hint=(0.8, 0.8))
        self.setting = BoxLayout(size_hint_x=2.5, orientation='vertical')
        title = Label(text='アップグレード', font_size=36)

        items = BoxLayout(size_hint_y=4, spacing=20, padding=(10, 10))

        temp0 = BoxLayout(orientation='vertical')
        temp0.add_widget(Label(text='最大取引量: 0.08BTC', font_size=20))
        temp0.add_widget(Button(text='無料アップグレード', font_size=20 , on_press=self.popup_upgrade0))
        items.add_widget(temp0)

        temp1 = BoxLayout(orientation='vertical')
        temp1.add_widget(Label(text='最大取引量: 0.4BTC', font_size=20))
        temp1.add_widget(Button(text='アップグレード', font_size=20 , on_press=self.popup_upgrade))
        items.add_widget(temp1)

        temp2 = BoxLayout(orientation='vertical')
        temp2.add_widget(Label(text='最大取引量: 1.0BTC', font_size=20))
        temp2.add_widget(Button(text='アップグレード', font_size=20, on_press=self.popup_upgrade))
        items.add_widget(temp2)

        temp3 = BoxLayout(orientation='vertical')
        temp3.add_widget(Label(text='取引量制限なし', font_size=20))
        temp3.add_widget(Button(text='アップグレード', font_size=20, on_press=self.popup_upgrade))
        items.add_widget(temp3)

        self.setting.add_widget(title)
        self.setting.add_widget(items)

        back_box = BoxLayout(padding=(250, 20), orientation='vertical', size_hint_y=1.5, spacing=10)
        back_box.add_widget(Button(text='戻る', on_press=self.upgrade_pop_close, background_normal=white_button))

        self.setting.add_widget(back_box)

        self.up_pop.add_widget(self.setting)
        self.up_pop.open()

    def upgrade_pop_close(self, *args):
        self.up_pop.dismiss()

    def ret_pop_bx(self, *args):
        self.popup = Popup(title='アップグレード', size_hint=(0.8, 0.8))
        popup_bx = BoxLayout(orientation='vertical')

        orientation_bx = BoxLayout(orientation='vertical')
        tx1 = '1.アップグレードコードを入力してください。'
        tx2 = '2.LISAを再起動してください。'
        lb1 = Label(text=tx1)
        lb2 = Label(text=tx2)
        for i in [lb1, lb2]:
            i.text_size = (850, 100)
            i.halign = 'left'
            i.valign = 'middle'
        orientation_bx.add_widget(lb1)
        orientation_bx.add_widget(lb2)
        popup_bx.add_widget(orientation_bx)

        purchase_box = BoxLayout(orientation='vertical', padding=(50, 20))
        purchase_button = Button(text='アップグレードコードを取得', on_press=self.go_rebellio)
        purchase_box.add_widget(purchase_button)
        popup_bx.add_widget(purchase_box)

        api_bx = BoxLayout(orientation='vertical', padding=(50, 40))
        self.btc_tx = TextInput(hint_text='アップグレードコードを入力', multiline=False)
        api_bx.add_widget(self.btc_tx)
        popup_bx.add_widget(api_bx)

        self.message_btc = Label(text='', size_hint_y=0.1)
        popup_bx.add_widget(self.message_btc)

        bt_bx = BoxLayout(orientation='vertical', padding=(180, 20), size_hint_y=1.2)
        bt_bx.add_widget(Button(text='アップグレード', on_press=self.auth_code))
        button_bx = BoxLayout(size_hint_y=1.3)
        cancel = Button(text='戻る', on_press=self.popup_close)
        button_bx.add_widget(cancel)
        bt_bx.add_widget(button_bx)
        popup_bx.add_widget(bt_bx)

        self.popup.content = popup_bx
        self.popup.open()

    def popup_upgrade0(self, *args):
        self.go_url = 'https://rebellio.jp/artificial-intelligence/lisa-free-upgrade'
        self.ret_pop_bx()

    def popup_upgrade(self, *args):
        self.go_url = 'https://rebellio.jp/item/lisa'
        self.ret_pop_bx()

    def go_rebellio(self, *args):
        webbrowser.open(self.go_url)

    def auth_code(self, *args):
        if self.btc_tx.text == '':
            self.message_btc.text = 'アップグレードコードを入力してください。'
        else:
            try:
                header = {'x-api-key': key}
                params = {'number': self.btc_tx.text, 'price': self.max_qty, 'address': 'dummy'}
                res = requests.get(register_payments_url, params=params, headers=header)
                if res.json()['amount']:
                    register_qty(res.json()['amount'])
                    self.message_btc.text = '成功しました。再起動してください。(最大取引量{}BTC)'.format(res.json()['amount'])
                else:
                    self.message_btc.text = '失敗しました。コードが正しいか、使用済みでないか、今のプランからアップグレード可能か確認してください。'
            except Exception as e:
                print(e)
                self.message_btc.text = 'エラー'


class PreScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_countdown = True
        self.orientation = 'vertical'
        Clock.schedule_interval(self.go_main, 3)

    def go_main(self, *args):
        self.is_countdown = False
        Clock.unschedule(self.go_main)
        self.clear_widgets()
        self.add_widget(MainScreen())


class MainApp(App):
    def build(self):
        self.icon = 'pics/rebellio-icon.png'
        self.title = 'LISA'
        self.root = root = PreScreen()
        root.bind(size=self._update_rect, pos=self._update_rect)
        with root.canvas:
            Color(0.1, 0.11, 0.11, 1)
            self.rect = Rectangle(size=root.size, pos=root.pos)
        wimg = Image(source='pics/lisa.png', size_hint_y = 2)
        logo = BoxLayout(padding=(0, 0))
        root.add_widget(logo)
        root.add_widget(wimg)
        root.add_widget(Label(text='読込中...', font_size=36))
        return root

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size


if __name__ == "__main__":
    try:
        MainApp().run()
    except Exception as e:
       print('ERROR!!')
       print(e)
       input()
