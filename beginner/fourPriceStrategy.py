#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'shubin'
# !/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'shubin'

import datetime
import time
from datetime import date

from tqsdk import TqApi, TqSim, TqAuth, TqBacktest, BacktestFinished, TargetPosTask

SYMBOL = ""
back_test_start = date(2022, 1, 1)
back_test_end = date(2022, 1, 1)
close_hour = 15
close_minute = 0

user = "shubin"
password = "Lishubin1013"
account = TqSim()

api = TqApi(
    account=account,
    backtest=TqBacktest(start_dt=back_test_start, end_dt=back_test_end),
    auth=TqAuth(user, password)
)
k_lines = api.get_kline_serial(symbol=SYMBOL, duration_seconds=24 * 60 * 60)
target_pos: TargetPosTask = TargetPosTask(api, SYMBOL)
position = api.get_position(SYMBOL, account)
quote = api.get_quote(SYMBOL)  # 获取指定合约的盘口行情

if __name__ == '__main__':
    try:
        print("策略开始")

        while True:
            api.wait_update()
            # 日期发生变动时，进入下一天
            if api.is_changing(k_lines[-1], "datetime"):
                # 策略核心是
                # 多头 当价格大于昨日high时，进入多单，止损点为今日的开盘价
                # 空头 当价格低于昨日low时，进入空单，止损点为今日的开盘价
                top_rail = k_lines.high[-2]
                low_rail = k_lines.low[-2]
                if api.is_changing(quote, "last_price"):
                    if quote.last_price > top_rail and position.pos_long == 0:
                        target_pos.set_target_volume(5)
                        print("多单，进入价格:{}".format(quote.last_price))
                        # 每次开单要记录日志
                    elif quote.last_price < low_rail and position.pos_short == 0:
                        target_pos.set_target_volume(-5)
                        print("空单，进入价格:{}".format(quote.last_price))
                    # 止损条件
                    elif (position.pos_long != 0 and quote.last_price < k_lines.open[-1]) or (
                            position.pos_short != 0 and quote.last_price > k_lines.open[-1]):
                        target_pos.set_target_volume(0)
                        print("止损, 止损价格:{},损益:{}".format(quote.last_price, position.position_profit))
                # 日内关闭
                if api.is_changing(quote, "datetime"):
                    now_time = datetime.datetime.strptime(quote.datetime, "%Y-%m-%d %H:%M:%S.%f")
                    if now_time.hour == close_hour and now_time.minute == close_minute:
                        target_pos.set_target_volume(0)
                        print("日内退出平仓，退出价格:{},损益:{}".format(quote.last_price, position.position_profit))
                        deadline = time.time() + 60  # 设置截止时间为当前时间的60秒以后
                        while api.wait_update(deadline=deadline):  # 等待60秒
                            pass

    except BacktestFinished as e:
        # 回测结束时会执行这里的代码
        api.close()
        # print(account.trade_log)  # 回测的详细信息
        print(account.tqsdk_stat)  # 回测时间内账户交易信息统计结果，其中包含以下字段
        # init_balance 起始资金
        # balance 结束资金
        # max_drawdown 最大回撤
        # profit_loss_ratio 盈亏额比例
        # winning_rate 胜率
        # ror 收益率
        # annual_yield 年化收益率
        # sharpe_ratio 年化夏普率
        # tqsdk_punchline 天勤点评
