import logging
import threading
import time

from chatrobot import DingtalkChatbot
from huobi_swap_client import Huobi_Swap_Client

logger = logging.getLogger('root')

# Huobi Main account
# Huobi_Access_Key = 'b00f2e77-be663014-125c4637-dbuqg6hkte'
# Huobi_Secret_Key = '53ea9f05-1d068deb-a314d834-9c290'

# alaric0001_macd
Huobi_Access_Key = '0b9e06a8-xa2b53ggfc-929af80b-d8c22'
Huobi_Secret_Key = '5f46f8db-27fc972a-1ad70984-fa622'

# dingding address info
dingding_address = 'https://oapi.dingtalk.com/robot/send?access_token=140d1e6686588c070a5e4edce39beb5feb74003450bbac8f3c53bfa34e079baa'

is_proxies = False

# order settings
contract_code = 'BTC-USDT'
lever_rate = 10
order_price_type='optimal_20'

# contract info
contract_decimal = 1

class MACD_strategy():

    def __init__(self):
        # strategy info
        self.strategy_account = 'Alaric test account'
        self.strategy_name = 'MACD strategy version 3'

        # dingding info
        self.xiaoding = DingtalkChatbot(dingding_address)

        # Swap client instance
        self.huobi_swap_client = Huobi_Swap_Client(Access_Key=Huobi_Access_Key,
                                                   Secret_Key=Huobi_Secret_Key,
                                                   is_proxies=is_proxies)

        # current account info
        self.max_leverage_rate = 10
        self.start_margin_balance = 0
        self.current_margin_balance = 0  # 账户权益
        self.current_margin_available = 0  # 可用保证金
        self.current_margin_frozen = 0  # 冻结保证金
        self.current_liquidation_price = 0  # 预估强平价格
        self.current_lever_rate = 0  # 杠杆倍数

        # tpsl info
        self.tpsl_volume = 0
        self.tpsl_direction = None
        self.tpsl_trigger_price = 0
        self.tpsl_order_type = None

        # current position info
        # buy position
        self.current_buy_volume = 0  # 当前多头总仓位
        self.current_buy_volume_available = 0  # 当前多头可用仓位
        self.current_buy_volume_frozen = 0  # 当前多头冻结仓位
        self.current_buy_cost_open = 0  # 多头开仓均价
        self.current_buy_position_margin = 0  # 多头持仓保证金
        # sell position
        self.current_sell_volume = 0  # 当前空头总仓位
        self.current_sell_volume_available = 0  # 当前空头可用仓位
        self.current_sell_volume_frozen = 0  # 当前空头冻结仓位
        self.current_sell_cost_open = 0  # 空头开仓均价
        self.current_sell_position_margin = 0  # 空头持仓保证金

        # quant model params
        self.period_short = 12
        self.period_long = 26
        self.period_dea = 9
        self.k_lines_count = 700

        # trade params
        self.trade_leverage = 1
        self.max_leverage = 10
        self.backup_stop_order_percent = 1.02

        self.macd = 0
        self.diff = 0
        self.trade_signal = 0
        self.trade_state = 'IDLE'

        self.trade_amount = 0

        self.current_working_day = None

        # market infomation
        self.current_market_price = float(
            self.huobi_swap_client.get_market_trade(contract_code=contract_code)['tick']['data'][0]['price']
        )

    '''quant model'''
    def get_MACD(self):
        k_lines = self.huobi_swap_client.get_k_lines(
                    contract_code=contract_code,
                    period='60min',
                    size=self.k_lines_count
                    )['data']
        while len(k_lines) != self.k_lines_count:
            time.sleep(1)
            k_lines = self.huobi_swap_client.get_k_lines(
                        contract_code=contract_code,
                        period='60min',
                        size=self.k_lines_count)['data']
        # print(k_lines)
        # print('newest kline is ',k_lines[self.k_lines_count-1])
        ema_1 = []
        ema_2 = []
        dea = []
        self.macd = 0
        # bar = 0
        ema_1.append(k_lines[0]['close'])
        ema_2.append(k_lines[0]['close'])
        self.diff = ema_1[-1] - ema_2[-1]
        dea.append(self.diff)
        for i in range(1, self.k_lines_count-1):
            ema_1.append(
                ema_1[-1] * ((self.period_short - 1) / (self.period_short + 1)) + k_lines[i]['close'] * (2 / (self.period_short + 1))
                )
            ema_2.append(
                ema_2[-1] * ((self.period_long - 1) / (self.period_long + 1)) + k_lines[i]['close'] * (2 / (self.period_long + 1))
                )
            self.diff = ema_1[-1] - ema_2[-1]
            dea.append(dea[-1] * ((self.period_dea - 1) / (self.period_dea + 1)) + self.diff * (2 / (self.period_dea + 1)))
            self.macd = self.diff - dea[-1]
            bar = 2 * (self.diff - dea[-1])
        if self.diff > 0 and self.macd > 0:
            self.trade_signal = 1
        elif self.diff < 0 and self.macd < 0:
            self.trade_signal = -1
        else:
            self.trade_signal = 0
        message = 'macd is %s, diff is %s, Trade signal is %s.' % (self.macd, self.diff, self.trade_signal)
        # print(message)
        # self.dingding_notice(message)

    '''trade logic'''
    def trade(self):
        current_hour = time.localtime(time.time()).tm_hour # 记录一下小时 用于播报
        last_hour = None
        while True:
            # 用thread的方式计算macd交易信号 防止由于网络问题导致程序中断
            MACD_thread = threading.Thread(target=self.get_MACD)
            MACD_thread.start()
            while MACD_thread.is_alive() is True:
                time.sleep(0.2)

            # 根据计算出的交易信号判断现在应该处在的状态：Long，Short or IDLE
            if self.trade_signal == 1: # 当前的仓位应处于多头状态
                self.get_trade_amount() # 获取根据当前仓位计算出的开仓数量
                check_position_thread = threading.Thread(target=self.check_position)
                check_position_thread.start()
                while check_position_thread.is_alive() is True:
                    time.sleep(0.2)

                if self.trade_state == 'IDLE': # 如果检测到目前仓位为空仓，开多仓，数量为trade amount
                    open_order_info = None
                    open_order_info = self.huobi_swap_client.create_order(contract_code = contract_code,
                                                                          volume = int(self.trade_amount),
                                                                          direction = 'buy',
                                                                          offset = 'open',
                                                                          lever_rate = lever_rate,
                                                                          order_price_type = order_price_type)
                    message = 'Current position is %s, \n' \
                              'Current status should be Long, amount should be %s \n ' \
                              'Operation: \n ' \
                              'Place long order, trade amount is %s. \n ' \
                              'Order info: \n ' \
                              '%s' %(
                                  self.trade_state,
                                  self.trade_amount,
                                  int(self.trade_amount),
                                  open_order_info
                              )
                    self.dingding_notice(message)

                elif self.trade_state == 'Short': # 如果检测到目前仓位为空头，平空仓后开多仓，开仓数量为trade amount
                    close_order_info = None
                    close_order_info = self.huobi_swap_client.create_order(contract_code = contract_code,
                                                                           volume = int(self.current_sell_volume),
                                                                           direction = 'buy',
                                                                           offset = 'close',
                                                                           lever_rate = lever_rate,
                                                                           order_price_type = order_price_type)
                    time.sleep(1)
                    open_order_info = None
                    open_order_info = self.huobi_swap_client.create_order(contract_code = contract_code,
                                                                          volume = int(self.trade_amount),
                                                                          direction = 'buy',
                                                                          offset = 'open',
                                                                          lever_rate = lever_rate,
                                                                          order_price_type = order_price_type)

                    message = 'Current position is %s, sell volume is %s. \n' \
                              'Current status should be Long, amount should be %s \n ' \
                              'Operation: \n ' \
                              'Close short position, close amount is %s \n ' \
                              'Close order info: \n ' \
                              '%s \n ' \
                              'Place long order, trade amount is %s. \n ' \
                              'Order info: \n ' \
                              '%s' %(
                                  self.trade_state, int(self.current_sell_volume),
                                  self.trade_amount,
                                  int(self.current_sell_volume),
                                  close_order_info,
                                  int(self.trade_amount),
                                  open_order_info
                              )
                    self.dingding_notice(message)

                elif self.trade_state == 'Long': # 如果检测到目前仓位为多头，则判断开仓数量是否正确，多退少补
                    if self.current_buy_volume > self.trade_amount: # 如果多头仓位大于交易数量，则平掉多于的部分
                        close_order_info = None
                        close_order_info = self.huobi_swap_client.create_order(contract_code = contract_code,
                                                                               volume = int(self.current_buy_volume-self.trade_amount),
                                                                               direction = 'sell',
                                                                               offset = 'close',
                                                                               lever_rate = lever_rate,
                                                                               order_price_type = order_price_type)
                        message = 'Current position is %s, buy volume is %s \n' \
                                  'Current status should be Long, amount should be %s \n ' \
                                  'Operation: \n ' \
                                  'Close long order, trade amount is %s. \n ' \
                                  'Close order info: \n ' \
                                  '%s' %(
                                      self.trade_state, self.current_buy_volume,
                                      self.trade_amount,
                                      int(self.current_buy_volume-self.trade_amount),
                                      close_order_info
                                  )
                        self.dingding_notice(message)

                    elif self.current_buy_volume < self.trade_amount: # 如果多头仓位小于交易数量，则补上不够的部分
                        open_order_info = None
                        open_order_info = self.huobi_swap_client.create_order(contract_code = contract_code,
                                                                              volume = int(self.trade_amount-self.current_buy_volume),
                                                                              direction = 'buy',
                                                                              offset = 'open',
                                                                              lever_rate = lever_rate,
                                                                              order_price_type = order_price_type)
                        message = 'Current position is %s, buy volume is %s \n' \
                                  'Current status should be Long, amount should be %s \n ' \
                                  'Operation: \n ' \
                                  'Open long order, trade amount is %s. \n ' \
                                  'Close order info: \n ' \
                                  '%s' %(
                                      self.trade_state, self.current_buy_volume,
                                      self.trade_amount,
                                      int(self.trade_amount-self.current_buy_volume),
                                      open_order_info
                                  )
                        self.dingding_notice(message)

                    else:
                        message = 'Current position is %s, buy volume is %s \n' \
                                  'Current status should be Long, amount should be %s \n ' \
                                  'Operation: \n ' \
                                  'Strategy Running Normal! No Futher Operation Needed! \n ' \
                                  %(
                                      self.trade_state, self.current_buy_volume,
                                      self.trade_amount
                                  )

                        if current_hour != last_hour and current_hour in [0, 4, 8, 12, 16, 20]:
                            self.dingding_notice(message)
                            last_hour = current_hour

            elif self.trade_signal == -1: # 当前的仓位应处于空头状态
                self.get_trade_amount() # 获取根据当前仓位计算出的开仓数量
                check_position_thread = threading.Thread(target=self.check_position)
                check_position_thread.start()
                while check_position_thread.is_alive() is True:
                    time.sleep(0.2)

                if self.trade_state == 'IDLE':# 如果检测到目前仓位为空仓，开空仓，数量为trade amount
                    open_order_info = None
                    open_order_info = self.huobi_swap_client.create_order(contract_code = contract_code,
                                                                          volume = int(self.trade_amount),
                                                                          direction = 'sell',
                                                                          offset = 'open',
                                                                          lever_rate = lever_rate,
                                                                          order_price_type = order_price_type)
                    message = 'Current position is %s, \n' \
                              'Current status should be Short, amount should be %s \n ' \
                              'Operation: \n ' \
                              'Place short order, trade amount is %s. \n ' \
                              'Order info: \n ' \
                              '%s' %(
                                  self.trade_state,
                                  self.trade_amount,
                                  int(self.trade_amount),
                                  open_order_info
                              )
                    self.dingding_notice(message)

                elif self.trade_state =='Long': # 如果检测到目前仓位为空头，平多后开空仓，开仓数量为trade amount
                    close_order_info = None
                    close_order_info = self.huobi_swap_client.create_order(contract_code = contract_code,
                                                                           volume = int(self.current_buy_volume),
                                                                           direction = 'sell',
                                                                           offset = 'close',
                                                                           lever_rate = lever_rate,
                                                                           order_price_type = order_price_type)
                    time.sleep(1)
                    open_order_info = None
                    open_order_info = self.huobi_swap_client.create_order(contract_code = contract_code,
                                                                          volume = int(self.trade_amount),
                                                                          direction = 'sell',
                                                                          offset = 'open',
                                                                          lever_rate = lever_rate,
                                                                          order_price_type = order_price_type)

                    message = 'Current position is %s, buy volume is %s. \n' \
                              'Current status should be Short, amount should be %s \n ' \
                              'Operation: \n ' \
                              'Close long position, close amount is %s \n ' \
                              'Close order info: \n ' \
                              '%s \n ' \
                              'Place short order, trade amount is %s. \n ' \
                              'Order info: \n ' \
                              '%s' %(
                                  self.trade_state, self.current_buy_volume,
                                  self.trade_amount,
                                  self.current_buy_volume,
                                  close_order_info,
                                  int(self.trade_amount),
                                  open_order_info
                              )
                    self.dingding_notice(message)

                elif self.trade_state == 'Short': # 如果检测到目前仓位为空头，则判断开仓数量是否正确，多退少补
                    if self.current_sell_volume > self.trade_amount: # 如果空头数量大于交易数量，则平掉多于的部分
                        close_order_info = None
                        close_order_info = self.huobi_swap_client.create_order(contract_code=contract_code,
                                                                               volume = int(self.current_sell_volume - self.trade_amount),
                                                                               direction = 'buy',
                                                                               offset='close',
                                                                               lever_rate = lever_rate,
                                                                               order_price_type= order_price_type)
                        message = 'Current position is %s, sell volume is %s \n' \
                                  'Current status should be Short, amount should be %s \n ' \
                                  'Operation: \n ' \
                                  'Close short order, trade amount is %s. \n ' \
                                  'Close order info: \n ' \
                                  '%s' %(
                                      self.trade_state, self.current_sell_volume,
                                      self.trade_amount,
                                      int(self.current_sell_volume - self.trade_amount),
                                      close_order_info
                                  )
                        self.dingding_notice(message)
                    elif self.current_sell_volume < self.trade_amount: # 如果空头数量小于交易数量，则补上不够的部分
                        open_order_info = None
                        open_order_info = self.huobi_swap_client.create_order(contract_code=contract_code,
                                                                              volume = int(self.trade_amount - self.current_sell_volume),
                                                                              direction = 'sell',
                                                                              offset='open',
                                                                              lever_rate = lever_rate,
                                                                              order_price_type = order_price_type)
                        message = 'Current position is %s, sell volume is %s \n' \
                                  'Current status should be Short, amount should be %s \n ' \
                                  'Operation: \n ' \
                                  'Open short order, trade amount is %s. \n ' \
                                  'Close order info: \n ' \
                                  '%s' %(
                                      self.trade_state, self.current_sell_volume,
                                      self.trade_amount,
                                      int(self.trade_amount - self.current_sell_volume),
                                      open_order_info
                                  )
                        self.dingding_notice(message)
                    else:
                        message = 'Current position is %s, sell volume is %s \n' \
                                  'Current status should be Short, amount should be %s \n ' \
                                  'Operation: \n ' \
                                  'Strategy Running Normal! No Futher Operation Needed! \n ' \
                                  %(
                                      self.trade_state, self.current_sell_volume,
                                      self.trade_amount
                                  )

                        if current_hour != last_hour and current_hour in [0, 4, 8, 12, 16, 20]:
                            self.dingding_notice(message)
                            last_hour = current_hour

            elif self.trade_signal == 0: # 当前的仓位应处于空仓状态
                self.get_trade_amount()
                check_position_thread = threading.Thread(target=self.check_position)
                check_position_thread.start()
                while check_position_thread.is_alive() is True:
                    time.sleep(0.2)

                if self.trade_state == 'IDLE': # 如果当前仓位为空仓则不需要进行任何操作
                    message = 'Current position is %s. \n' \
                              'Current status should be IDLE \n' \
                              'Operation: \n' \
                              'Strategy Running Normal! No Futher Operation Needed! \n ' %(
                                  self.trade_state
                              )

                    if current_hour != last_hour and current_hour in [0, 4, 8, 12, 16, 20]:
                        self.dingding_notice(message)
                        last_hour = current_hour

                elif self.trade_state =='Short': # 如果当前仓位为空头，则应平掉所有的空头仓位
                    close_order_info = None
                    close_order_info = self.huobi_swap_client.create_order(contract_code=contract_code,
                                                                           volume=int(self.current_sell_volume),
                                                                           direction = 'buy',
                                                                           offset = 'close',
                                                                           lever_rate = lever_rate,
                                                                           order_price_type=order_price_type)
                    message = 'Current position is %s, sell volume is %s. \n' \
                              'Current status should be IDLE \n' \
                              'Operation: \n' \
                              'Close short position, close amount is %s \n ' \
                              'Close order info: \n' \
                              '%s \n ' %(
                                  self.trade_state, self.current_sell_volume,
                                  int(self.current_sell_volume),
                                  close_order_info
                              )
                    self.dingding_notice(message)

                elif self.trade_state == 'Long': # 如果当前的仓位为空头，则应平掉所有的多头仓位
                    close_order_info = None
                    close_order_info = self.huobi_swap_client.create_order(contract_code = contract_code,
                                                                           volume = int(self.current_buy_volume),
                                                                           direction = 'sell',
                                                                           offset = 'close',
                                                                           lever_rate = lever_rate,
                                                                           order_price_type = order_price_type)
                    message = 'Current position is %s, lone volume is %s. \n' \
                              'Current status should be IDLE \n' \
                              'Operation: \n' \
                              'Close long position, close amount is %s \n' \
                              'Close order info: \n' \
                              '%s \n ' %(
                                  self.trade_state, int(self.current_buy_volume),
                                  int(self.current_buy_volume),
                                  close_order_info
                              )
                    self.dingding_notice(message)
            stop_order_thread = threading.Thread(target=self.stop_order)
            stop_order_thread.start()
            while stop_order_thread.is_alive() is True:
                time.sleep(0.2)
            time.sleep(15)

    def stop_order(self):
        check_position_thread = threading.Thread(target=self.check_position)
        check_position_thread.start()
        while check_position_thread.is_alive() is True:
            time.sleep(0.2)

        if self.trade_state == 'IDLE': # 检测到仓位为空仓，此时应该没有止损单，如果有就撤销掉止损单
            if self.tpsl_direction != None or \
                self.tpsl_volume != 0 or \
                self.tpsl_trigger_price != 0:
                cancel_order_info = self.huobi_swap_client.cancel_tpsl_order_all(contract_code = contract_code)
                message = f'''\n
                            Current trade status is IDLE, but tpsl order exist. \n
                            TPSL order should be canceled. \n 
                            Cancel order info is: \n 
                            {cancel_order_info}
                            '''
                self.dingding_notice(message)

        elif self.trade_state == 'Long': # 检查到仓位为多头，如果方向，价格或数量不对，则取消订单重新下单
            stopPx = self.current_buy_cost_open / self.backup_stop_order_percent
            if self.tpsl_direction != 'sell' or \
                self.tpsl_volume != round(self.current_buy_volume,1) or \
                self.tpsl_trigger_price != stopPx:

                cancel_order_info = self.huobi_swap_client.cancel_tpsl_order_all(contract_code = contract_code)
                time.sleep(1)
                stop_order = self.huobi_swap_client.create_tpsl_order(contract_code = contract_code,
                                                                      direction = 'sell',
                                                                      volume = int(self.current_buy_volume),
                                                                      sl_trigger_price = self.format_price(stopPx),
                                                                      sl_order_price_type = order_price_type
                                                                      )
                message = f'''\n
                            Current trade status is Long \n 
                            TPSL direction is {self.tpsl_direction}; should be sell \n 
                            TPSL volume is {self.tpsl_volume}; should be {self.current_buy_volume} \n 
                            TPSL trigger price is {self.tpsl_trigger_price}; should be {stopPx} \n 
                            TPSL order is wrong; cancel order and replace \n 
                            Cancel order info: \n 
                            {cancel_order_info} \n 
                            Stop order info: \n 
                            {stop_order}
                            '''
                self.dingding_notice(message)

        elif self.trade_state == 'Short': # 检查到仓位为空头，如果方向，价格或数量不对，则取消订单重新下单
            stopPx = self.current_sell_cost_open * self.backup_stop_order_percent
            if self.tpsl_direction != 'buy' or \
                self.tpsl_volume != round(self.current_sell_volume,1) or \
                self.tpsl_trigger_price != stopPx:
                cancel_order_info = self.huobi_swap_client.cancel_tpsl_order_all(contract_code = contract_code)
                time.sleep(1)
                stop_order = self.huobi_swap_client.create_tpsl_order(contract_code = contract_code,
                                                                      direction = 'buy',
                                                                      volume = int(self.current_sell_volume),
                                                                      sl_trigger_price = self.format_price(stopPx),
                                                                      sl_order_price_type = order_price_type
                                                                      )
                message = f'''\n
                            Current trade status is Short \n 
                            TPSL direction is {self.tpsl_direction}; should be buy \n 
                            TPSL volume is {self.tpsl_volume}; should be {self.current_sell_volume} \n 
                            TPSL trigger price is {self.tpsl_trigger_price}; should be {stopPx} \n 
                            TPSL order is wrong; cancel order and replace \n 
                            Cancel order info: \n 
                            {cancel_order_info} \n 
                            Stop order info: \n 
                            {stop_order}
                            '''
                self.dingding_notice(message)



    '''account info'''
    def get_current_account_position_info(self):
        # current account info
        self.current_margin_balance = 0  # 账户权益
        self.current_margin_available = 0  # 可用保证金
        self.current_margin_frozen = 0  # 冻结保证金
        self.current_liquidation_price = 0  # 预估强平价格
        self.current_lever_rate = 0  # 杠杆倍数
        # current position info
        # buy position
        self.current_buy_volume = 0  # 当前多头总仓位
        self.current_buy_volume_available = 0  # 当前多头可用仓位
        self.current_buy_volume_frozen = 0  # 当前多头冻结仓位
        self.current_buy_cost_open = 0  # 多头开仓均价
        self.current_buy_position_margin = 0  # 多头持仓保证金
        # sell position
        self.current_sell_volume = 0  # 当前空头总仓位
        self.current_sell_volume_available = 0  # 当前空头可用仓位
        self.current_sell_volume_frozen = 0  # 当前空头冻结仓位
        self.current_sell_cost_open = 0  # 空头开仓均价
        self.current_sell_position_margin = 0  # 空头持仓保证金
        current_position = self.huobi_swap_client.get_swap_account_position_info(contract_code=contract_code)

        if current_position['status'] == 'ok':
            if len(current_position['data']) > 0:
                self.current_margin_balance = current_position['data'][0]['margin_balance']  # 账户权益
                self.current_margin_available = current_position['data'][0]['margin_available']  # 可用保证金
                self.current_margin_frozen = current_position['data'][0]['margin_frozen']  # 冻结保证金
                self.current_liquidation_price = current_position['data'][0]['liquidation_price']  # 预估强平价格
                self.current_lever_rate = current_position['data'][0]['lever_rate']  # 杠杆倍数
                message = 'Account info: \n' \
                          'margin balance is %s, margin available is %s, margin frozen is %s, liquidation price is ' \
                          '%s, lever rate is %s.\n Current time: %s.\n' \
                          % (self.current_margin_balance,
                             self.current_margin_available,
                             self.current_margin_frozen,
                             self.current_liquidation_price,
                             self.current_lever_rate,
                             time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()))
                # print(message)
                if len(current_position['data'][0]['positions']) > 0:
                    for i in current_position['data'][0]['positions']:
                        if i['direction'] == 'buy':
                            self.current_buy_volume = i['volume']  # 当前多头总仓位
                            self.current_buy_volume_available = i['available']  # 当前多头可用仓位
                            self.current_buy_volume_frozen = i['frozen']  # 当前多头冻结仓位
                            self.current_buy_cost_open = i['cost_open']  # 多头开仓均价
                            self.current_buy_position_margin = i['position_margin']  # 多头持仓保证金
                        if i['direction'] == 'sell':
                            self.current_sell_volume = i['volume']  # 当前空头总仓位
                            self.current_sell_volume_available = i['available']  # 当前空头可用仓位
                            self.current_sell_volume_frozen = i['frozen']  # 当前空头冻结仓位
                            self.current_sell_cost_open = i['cost_open']  # 空头开仓均价
                            self.current_sell_position_margin = i['position_margin']  # 空头持仓保证金

                    message = 'Buy position: \n' \
                              'buy volume is %s, buy volume available is %s, buy volume frozen is: %s, \n' \
                              'buy cost open is %s, buy position margin is %s. \n \n' \
                              'Sell position: \n' \
                              'sell volume is %s, sell volume available is %s, sell volume frozen is: %s, \n' \
                              'sell cost open is %s, sell position margin is %s.\n' \
                              'Current time: %s.' \
                              % (self.current_buy_volume,
                                 self.current_buy_volume_available,
                                 self.current_buy_volume_frozen,
                                 self.current_buy_cost_open,
                                 self.current_buy_position_margin,
                                 self.current_sell_volume,
                                 self.current_sell_volume_available,
                                 self.current_sell_volume_frozen,
                                 self.current_sell_cost_open,
                                 self.current_sell_position_margin,
                                 time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                                 )
                    # print(message)
                else:
                    message = 'No position info'
                    # print(message)
                    # logger.info(message)
            else:
                message = 'Cannot get current account and position infomation. (situation 2)'
                print(message)
                # logger.info(message)
        else:
            message = 'Cannot get current account and position infomation. (situation 1)'
            print(message)
            # logger.info(message)

    def check_position(self):
        self.get_current_account_position_info()
        time.sleep(1.5)
        if self.current_buy_volume == self.current_sell_volume:
            self.trade_state = 'IDLE'
        elif self.current_buy_volume > self.current_sell_volume:
            self.trade_state = 'Long'
        else:
            self.trade_state = 'Short'
        # print('Trade status is: ',self.trade_state)

    def get_trade_amount(self):
        market_price_thread = threading.Thread(target=self.get_current_price)
        market_price_thread.start()
        while market_price_thread.is_alive() is True:
            time.sleep(0.2)
        # print('Current market price is: ',self.current_market_price)

        get_account_thread = threading.Thread(target=self.get_current_account_position_info)
        get_account_thread.start()
        while get_account_thread.is_alive() is True:
            time.sleep(0.2)
        # print('Current margin balance is ', self.current_margin_balance)

        self.trade_amount = int(self.current_margin_balance / (self.current_market_price * 0.001) * self.trade_leverage)
        # print('trade amount is: ', self.trade_amount)

    def check_tpsl_openorders(self):
        openorders_info = self.huobi_swap_client.get_swap_tpsl_openorders(contract_code=contract_code)
        print(openorders_info)
        self.tpsl_volume = 0
        self.tpsl_direction = None
        self.tpsl_trigger_price = 0
        self.tpsl_order_type = None
        message = ''
        if openorders_info['status'] =='ok':
            if len(openorders_info['data']['orders']) != 0:
                self.tpsl_volume = int(openorders_info['data']['orders'][0]['volume'])
                self.tpsl_direction = openorders_info['data']['orders'][0]['direction']
                self.tpsl_trigger_price = openorders_info['data']['orders'][0]['trigger_price']
                self.tpsl_order_type = openorders_info['data']['orders'][0]['tpsl_order_type']
                message = 'tpsl direction is: %s \n' \
                          'tpsl_volume is: %s \n' \
                          'tpsl_trigger_price is: %s \n' \
                          'tpsl_order_type is: %s. \n' %(
                              self.tpsl_direction,
                              self.tpsl_volume,
                              self.tpsl_trigger_price,
                              self.tpsl_order_type
                          )
            else:
                message = 'There is no tpsl order'
        else:
            message = 'Cannot get tpsl order info'
        print(message)

    '''market info'''
    def get_current_price(self):
        self.current_market_price = float(
            self.huobi_swap_client.get_market_trade(contract_code=contract_code)['tick']['data'][0]['price']
        )

    '''tools'''
    # dingding post
    def ding_thread(self, out):
        self.xiaoding.send_text(out, is_at_all=False)

    def dingding_notice(self, message=None):
        self.get_current_account_position_info()
        basic_info = '--------------------------------\n' \
                     'Strategy name: %s \n' \
                     'Contract code: %s \n' \
                     'Current long position: %s \n' \
                     'Current short position: %s \n' \
                     'Local time: %s \n ' \
                     '--------------------------------\n' \
                     % (self.strategy_name,
                        contract_code,
                        self.current_buy_volume,
                        self.current_sell_volume,
                        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        out = message + basic_info
        t = threading.Thread(target=self.ding_thread, args=(out,), )
        t.start()

    def format_price(self, num):
        price = round(num, contract_decimal)
        return price

    def cancel_order_all(self):
        self.huobi_swap_client.cancel_order_by_symbol(contract_code=contract_code)
        self.huobi_swap_client.cancel_tpsl_order_all(contract_code=contract_code)

test = MACD_strategy()
test.trade()
# test.trade_start()
# test.get_MACD()
# test.check_tpsl_openorders()



# test.trade()

# test.check_position()
# print(test.huobi_swap_client.get_swap_account_position_info(contract_code=contract_code))
# test.get_current_account_position_info()
# test.xiaoding.send_text('strategy test message',is_at_all=False)
# test.dingding_notice('test')
# test.get_MACD()
# test.in_idle()
# aa = test.huobi_swap_client.cancel_order_by_symbol(contract_code=contract_code)
# print(aa)

# aa = test.huobi_swap_client.cancel_tpsl_order_all(contract_code=contract_code)
# print(aa)
# test.check_position()

# test.get_trade_amount()

# test.in_idle()

# aa = test.huobi_swap_client.create_tpsl_order(contract_code=contract_code,direction='sell',volume=1,
#                                          tp_trigger_price=34500,tp_order_price_type='optimal_5')
# print(aa)
# aa = test.huobi_swap_client.create_tpsl_order(contract_code=contract_code,direction='sell',volume=2,
#                                               sl_trigger_price=36023.5,sl_order_price_type='optimal_20')
# print(aa)

# print(test.huobi_swap_client.cancel_tpsl_order(contract_code=contract_code,order_id=805871093956476929))