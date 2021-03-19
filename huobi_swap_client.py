import requests
from requests import Request
from request_manager import RequestManager
import datetime
import hashlib
import time
import random,string
import base64
import hmac
import urllib
import urllib.parse
import json

# Access_Key = 'b00f2e77-be663014-125c4637-dbuqg6hkte'
# Secret_Key =  '53ea9f05-1d068deb-a314d834-9c290'

class Huobi_Swap_Client():

    def __init__(self, Access_Key, Secret_Key, is_proxies = False):
        self.Access_Key = Access_Key
        self.Secret_Key = Secret_Key
        self.is_proxies = is_proxies
        # self.BASE_URL = 'https://api.hbdm.com/' # for vpn
        # self.BASE_URL = 'https://api.hbdm.vn/' # for aws
        self.BASE_URL = 'https://api.btcgateway.pro/' # for test

    def utc_now(self):
        return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')

    def generate_signature(self, method, params, request_path):

        if request_path.startswith("http://") or request_path.startswith("https://"):
            host_url = urllib.parse.urlparse(request_path).hostname.lower()
            request_path = '/' + '/'.join(request_path.split('/')[3:])
        else:
            host_url = urllib.parse.urlparse(self.BASE_URL).hostname.lower()
        sorted_params = sorted(params.items(), key=lambda d: d[0], reverse=False)
        encode_params = urllib.parse.urlencode(sorted_params)

        payload = [method, host_url, request_path, encode_params]
        payload = "\n".join(payload)
        payload = payload.encode()

        secret_key = self.Secret_Key.encode()
        digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
        signature = base64.b64encode(digest)
        # signature = signature.decode()
        return signature

    '''合约资产接口'''
    # 【逐仓】获取用户账户信息 该接口仅支持逐仓模式。
    def get_account_info(self,contract_code=None):
        method = "POST"
        path = "linear-swap-api/v1/swap_account_info"
        url = self.BASE_URL + path
        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)
        data = {
            'contract_code': contract_code
        }
        data = json.dumps(data, separators=(',', ':'))

        my_request = Request(
            method=method,
            url=url,
            data=data,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    # 【逐仓】获取用户持仓信息 该接口仅支持逐仓模式。
    def get_swap_position_info(self,contract_code=None):
        method = "POST"
        path = "linear-swap-api/v1/swap_position_info"
        url = self.BASE_URL + path
        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        data = {
            'contract_code': contract_code
        }
        data = json.dumps(data, separators=(',', ':'))

        my_request = Request(
            method=method,
            url=url,
            data=data,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    # 【逐仓】获取用户账户和持仓信息 该接口仅支持逐仓模式。
    def get_swap_account_position_info(self,contract_code=None):
        method = "POST"
        path = "linear-swap-api/v1/swap_account_position_info"
        url = self.BASE_URL + path
        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        data = {
            'contract_code': contract_code
        }
        data = json.dumps(data, separators=(',', ':'))

        my_request = Request(
            method=method,
            url=url,
            data=data,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    # 【逐仓】查询母账户下所有子账户资产信息 该接口仅支持逐仓模式。
    def get_swap_sub_account_list(self,contract_code=None):
        method = "POST"
        path = "linear-swap-api/v1/swap_sub_account_list"
        url = self.BASE_URL + path
        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        data = {
            'contract_code': contract_code
        }
        data = json.dumps(data, separators=(',', ':'))

        my_request = Request(
            method=method,
            url=url,
            data=data,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    # 【通用】查询用户财务记录 该接口支持全仓模式和逐仓模式
    def get_swap_financial_record(self,margin_account):
        method = "POST"
        path = "linear-swap-api/v1/swap_financial_record"
        url = self.BASE_URL + path
        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        data = {
            'margin_account': margin_account
        }
        data = json.dumps(data, separators=(',', ':'))

        my_request = Request(
            method=method,
            url=url,
            data=data,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    '''行情数据'''
    # 【通用】获取合约信息 该接口支持全仓模式和逐仓模式
    def get_market_info(self, contract_code = None):
        method = 'GET'
        path = 'linear-swap-api/v1/swap_contract_info'
        url = self.BASE_URL + path

        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params['contract_code'] = contract_code
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        my_request = Request(
            method=method,
            url=self.BASE_URL + path,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    # 【通用】获取合约指数信息
    def get_swap_index(self,contract_code):
        method = 'GET'
        path = 'linear-swap-api/v1/swap_index'
        url = self.BASE_URL + path
        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params['contract_code'] = contract_code
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        my_request = Request(
            method=method,
            url=self.BASE_URL + path,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    # 【通用】获取合约最高限价和最低限价
    def get_swap_price_limit(self,contract_code):
        method = 'GET'
        path = 'linear-swap-api/v1/swap_price_limit'
        url = self.BASE_URL + path
        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params['contract_code'] = contract_code
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        my_request = Request(
            method=method,
            url=self.BASE_URL + path,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    # 【通用】获取行情深度数据
    def get_depth(self,contract_code,type='step0'):
        method = 'GET'
        path = 'linear-swap-ex/market/depth'
        url = self.BASE_URL + path
        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params['contract_code'] = contract_code
        params['type'] = type
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        my_request = Request(
            method=method,
            url=self.BASE_URL + path,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    # 【通用】获取K线数据
    def get_k_lines(self, contract_code, period,size=150):
        method = 'GET'
        path = 'linear-swap-ex/market/history/kline'
        url = self.BASE_URL + path

        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params['contract_code'] = contract_code
        params['period'] = period
        params['size'] = size
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        my_request = Request(
            method=method,
            url=self.BASE_URL + path,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    # 【通用】获取市场最近成交记录
    def get_market_trade(self,contract_code):
        method = 'GET'
        path = 'linear-swap-ex/market/trade'
        url = self.BASE_URL + path
        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params['contract_code'] = contract_code
        params['type'] = type
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        my_request = Request(
            method=method,
            url=self.BASE_URL + path,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    # 【通用】批量获取市场最近成交记录
    def get_market_history_trade(self,contract_code,size=10):
        method = 'GET'
        path = 'linear-swap-ex/market/history/trade'
        url = self.BASE_URL + path
        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params['contract_code'] = contract_code
        params['size'] = size
        params['type'] = type
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        my_request = Request(
            method=method,
            url=self.BASE_URL + path,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    def get_funding_rate(self,contract_code):
        method = 'GET'
        path = 'linear-swap-api/v1/swap_funding_rate'
        url = self.BASE_URL + path

        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params['contract_code'] = contract_code
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        my_request = Request(
            method=method,
            url=self.BASE_URL + path,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    def get_market_trade(self,contract_code):
        method = 'GET'
        path = 'linear-swap-ex/market/trade'
        url = self.BASE_URL + path

        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params['contract_code'] = contract_code
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        my_request = Request(
            method=method,
            url=self.BASE_URL + path,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    '''订单类'''
    def create_order(self,contract_code,volume,direction,offset,lever_rate,order_price_type,price=None):
        method = 'POST'
        path = 'linear-swap-api/v1/swap_order'
        url = self.BASE_URL + path

        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        data = {}
        data['contract_code'] = contract_code
        data['volume'] = volume
        data['direction'] = direction
        data['offset'] = offset
        data['lever_rate'] = lever_rate
        data['order_price_type'] = order_price_type
        data['price'] = price

        data = json.dumps(data, separators=(',', ':'))

        my_request = Request(
            method=method,
            url=url,
            data=data,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    def cancel_order(self,contract_code,order_id):
        method = 'POST'
        path = 'linear-swap-api/v1/swap_cancel'
        url = self.BASE_URL + path

        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        data = {}
        data['contract_code'] = contract_code
        data['order_id'] = order_id

        data = json.dumps(data, separators=(',', ':'))

        my_request = Request(
            method=method,
            url=url,
            data=data,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    def cancel_order_by_symbol(self,contract_code):
        method = 'POST'
        path = 'linear-swap-api/v1/swap_cancelall'
        url = self.BASE_URL + path

        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        data = {}
        data['contract_code'] = contract_code

        data = json.dumps(data, separators=(',', ':'))

        my_request = Request(
            method=method,
            url=url,
            data=data,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    def get_open_orders(self, contract_code):
        method = 'POST'
        path = 'linear-swap-api/v1/swap_openorders'
        url = self.BASE_URL + path

        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        data = {}
        data['contract_code'] = contract_code

        data = json.dumps(data, separators=(',', ':'))

        my_request = Request(
            method=method,
            url=url,
            data=data,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    # 市价买单amount为订单交易额 市价卖单amount为数量
    def create_batch_order(self,symbol,type,amount,price=None,stopprice=None,operator=None):
        account_id = self.Swap_account_id
        method = 'POST'
        path = '/v1/order/batch-orders'
        url = self.BASE_URL + path

        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)
        total_list=[]
        if stopprice is None:
            for i in range(len(amount)):
                data = {}
                data['account-id'] = account_id
                data['symbol'] = symbol
                data['type'] = type
                data['amount'] = str(amount[i])
                data['price'] = str(price[i])
                #data['operator'] = operator
                #data = json.dumps(data, separators=(',', ':'))
                total_list.append(data)
            total_list = json.dumps(total_list)

        elif stopprice is not None:
            for i in range(len(amount)):
                data = {}
                data['account-id'] = account_id
                data['symbol'] = symbol
                data['type'] = type
                data['amount'] = str(amount[i])
                data['price'] = str(price[i])
                data['stop-price'] = str(stopprice[i])
                #data['operator'] = operator
                #data = json.dumps(data, separators=(',', ':'))
                total_list.append(data)
            total_list=json.dumps(total_list)
        my_request = Request(
            method=method,
            url=url,
            data=total_list,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    # 基于order_id进行撤单
    def cancel_order_by_id(self,order_id):
        method = 'POST'
        path = '/v1/order/orders/'+order_id+'/submitcancel'
        url = self.BASE_URL + path
        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)
        my_request = Request(
            method=method,
            url=url,
            # data=data,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    #可以取消五十条
    def cancel_batch_order_by_id(self,order_ids):
        method = 'POST'
        path = '/v1/order/orders/batchcancel'
        url = self.BASE_URL + path
        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)
        data={}
        data['order-ids']=order_ids
        data=json.dumps(data, separators=(',', ':'))
        my_request = Request(
            method=method,
            url=url,
            data=data,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    '''触发类'''
    def get_swap_tpsl_openorders(self, contract_code):
        method = 'POST'
        path = 'linear-swap-api/v1/swap_tpsl_openorders'
        url = self.BASE_URL + path
        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        data = {}
        data['contract_code'] = contract_code

        data = json.dumps(data, separators=(',', ':'))

        my_request = Request(
            method=method,
            url=url,
            data=data,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)


    def create_tpsl_order(self, contract_code, direction, volume,
                          tp_trigger_price = None, tp_order_price = None, tp_order_price_type = None,
                          sl_trigger_price = None, sl_order_price = None, sl_order_price_type = None):
        method = 'POST'
        path = 'linear-swap-api/v1/swap_tpsl_order'
        url = self.BASE_URL + path

        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        data = {}
        data['contract_code'] = contract_code
        data['volume'] = volume
        data['direction'] = direction

        data['tp_trigger_price'] = tp_trigger_price
        data['tp_order_price'] = tp_order_price
        data['tp_order_price_type'] = tp_order_price_type

        data['sl_trigger_price'] = sl_trigger_price
        data['sl_order_price'] = sl_order_price
        data['sl_order_price_type'] = sl_order_price_type

        data = json.dumps(data, separators=(',', ':'))

        my_request = Request(
            method=method,
            url=url,
            data=data,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    def cancel_tpsl_order(self, contract_code, order_id):
        method = 'POST'
        path = 'linear-swap-api/v1/swap_tpsl_cancel'
        url = self.BASE_URL + path

        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        data = {}
        data['contract_code'] = contract_code
        data['order_id'] = order_id

        data = json.dumps(data, separators=(',', ':'))

        my_request = Request(
            method=method,
            url=url,
            data=data,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)

    def cancel_tpsl_order_all(self, contract_code, direction = None):
        method = 'POST'
        path = 'linear-swap-api/v1/swap_tpsl_cancelall'
        url = self.BASE_URL + path

        params = {
            'SignatureMethod': 'HmacSHA256',
            'SignatureVersion': '2',
            'AccessKeyId': self.Access_Key,
            'Timestamp': self.utc_now(),
        }
        params["Signature"] = self.generate_signature(method, params, url)
        params = urllib.parse.urlencode(params)

        data = {}
        data['contract_code'] = contract_code
        data['direction'] = direction

        data = json.dumps(data, separators=(',', ':'))

        my_request = Request(
            method=method,
            url=url,
            data=data,
            params=params
        )
        return RequestManager().send_request(my_request, self.is_proxies)



if __name__ == '__main__':
    aa = Huobi_Swap_Client(Access_Key=Access_Key, Secret_Key=Secret_Key, is_proxies=False)
    # print(aa.get_swap_tpsl_openorders(contract_code='BTC-USDT'))

    '''公共信息类'''
    # print(aa.get_market_info(contract_code='BTC-USDT'))
    # print(aa.get_swap_index(contract_code='BTC-USDT'))
    # print(aa.get_swap_price_limit(contract_code='BTC-USDT'))
    # print(aa.get_depth(contract_code='BTC-USDT'))
    # print(aa.get_k_lines(contract_code='BTC-USDT',period='5min'))
    # print(aa.get_market_trade(contract_code='BTC-USDT'))
    # print(aa.get_market_history_trade(contract_code='BTC-USDT',size=10))

    # print(aa.get_funding_rate(contract_code='BTC-USDT'))
    # print(aa.get_market_trade(contract_code='BTC-USDT'))

    '''账户信息'''
    # print(aa.get_account_info(contract_code='BTC-USDT'))
    # print(aa.get_swap_position_info(contract_code='BTC-USDT'))
    # print(aa.get_swap_account_position_info(contract_code='BTC-USDT'))
    # print(aa.get_swap_sub_account_list(contract_code='BTC-USDT'))
    # print(aa.get_swap_financial_record(margin_account='BTC-USDT'))

    '''订单类'''
    # print(aa.create_order(contract_code='BTC-USDT', volume=1, direction='buy', offset='open', lever_rate=10, order_price_type='limit', price=13500))
    # print(aa.create_order(contract_code='BTC-USDT', volume=1, direction='buy', offset='open', lever_rate=10,
    #                       order_price_type="opponent"))
    # print(aa.create_order(contract_code='BTC-USDT', volume=1, direction='sell', offset='close', lever_rate=10,
    #                       order_price_type="opponent"))

    # print(aa.create_order(contract_code='BTC-USDT', volume=1, direction='sell', offset='open', lever_rate=10,
    #                       order_price_type='limit', price=14000))
    # print(aa.create_order(contract_code='BTC-USDT', volume=1, direction='sell', offset='open', lever_rate=10,
    #                       order_price_type="opponent"))
    # print(aa.create_order(contract_code='BTC-USDT', volume=2, direction='buy', offset='close', lever_rate=10,
    #                       order_price_type="opponent"))

    # print(aa.cancel_order(contract_code='BTC-USDT',order_id='771031078055284736'))
    # print(aa.cancel_order_by_symbol(contract_code='BTC-USDT'))

    # print(aa.get_open_orders(contract_code='BTC-USDT'))

    # print(aa.get_account_id())

    # print(aa.get_account_balance())
    '''交易类'''
    # print(int(round(time.time() * 1000)))
    # print(aa.create_order(symbol='eosusdt', type='buy-limit',amount='3.0',price= '2'))
    # print(aa.create_order(symbol='eosusdt', type='sell-market', amount='3.8102'))
    # print(aa.create_order(symbol='eosusdt', type='buy-limit', amount='5.0', price='2'))
    # print(aa.get_open_orders(symbol='eosusdt')['data'])
    # print(len(aa.get_open_orders(symbol='eosusdt')['data']))
    # print(aa.cancel_order_by_id(order_id='52618611327105'))
    # # aa.cancel_order_all(symbol='eosusdt')
    #print(aa.create_batch_order(symbol='eosusdt', type='buy-limit',amount=[5,2,3],price=[1,2,3]))

    # print(aa.get_history_orders(symbol='eosusdt',state='submitted',start_time='1594199382393'))
    # print(aa.cancel_batch_order_by_id(order_ids=['']))


    # print(aa.apply_borrow_money(symbol='eosusdt', currency="btc", amount="0.0000000002"))

    # print(aa.get_k_lines(symbol='btcusdt',period='5min'))
    # print(aa.get_ticker(symbol='dotusdt'))
    # print(aa.get_symbols())

    # print(aa.create_batch_order(symbol='dotusdt', type='sell-limit', amount=['1','1','1','1','1'], price=['10','11','12', '13','14']))

    # print(aa.create_batch_order(symbol='dotusdt', type='sell-limit', amount=[1, 1, 1, 1,1],
    #                             price=[10, 11, 12, 13, 14]))

    # print(aa.create_tpsl_order(contract_code='BTC-USDT', direction='sell',volume=1,sl_trigger_price=45613.4,sl_order_price_type='optimal_5'))
