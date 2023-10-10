#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'shubin'

from datetime import date, datetime, time

from tqsdk import TqApi, TqSim, TqAuth, TqBacktest, BacktestFinished, TargetPosTask

SYMBOL = "SHFE.au1812"
back_test_start = date(2018, 11, 13)
back_test_end = date(2018, 11, 28)
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
quote = api.get_quote(SYMBOL)

dual_N = 5
dual_k1 = 0.2
dual_k2 = 0.2


def dual_range(k_lines):
    current_open = k_lines.iloc[-1]["open"]
    hh = max(k_lines[-dual_N - 1:-1]["high"])
    lc = min(k_lines[-dual_N - 1:-1]["close"])
    hc = max(k_lines[-dual_N - 1:-1]["close"])
    ll = min(k_lines[-dual_N - 1:-1]["low"])
    range = max(hh - lc, hc - ll)
    dual_top = current_open + range * dual_k1
    dual_bottom = current_open - range * dual_k2
    print("开盘价:{},上轨:{},下轨:{}".format(current_open, dual_top, dual_bottom))
    return dual_top, dual_bottom


top_rail, low_rail = dual_range(k_lines)

if __name__ == '__main__':
    try:
        print("策略开始")

        while True:
            api.wait_update()

            # 每日更新一次上下轨
            if api.is_changing(k_lines, ["datetime", "open"]):
                top_rail, low_rail = dual_range(k_lines)

            if api.is_changing(quote, "last_price"):
                if position.pos_long == 0 and position.pos_short == 0:
                    if quote.last_price > top_rail:
                        target_pos.set_target_volume(20)
                        print("当日价格超过上轨, 多单入场价格:{}".format(quote.last_price))

                    elif quote.last_price < low_rail:
                        target_pos.set_target_volume(-20)
                        print("当日价格超过下轨, 空单入场价格:{}".format(quote.last_price))
                elif position.pos_long > 0:
                    if quote.last_price < low_rail:
                        target_pos.set_target_volume(-20)
                        print("当日价格超过下轨,多单止损,多单损益:{}, 空单入场价格:{}".format(position.position_profit,
                                                                                              quote.last_price))
                    else:
                        print("多单继续持仓")
                elif position.pos_short > 0:
                    if quote.last_price > top_rail:
                        target_pos.set_target_volume(20)
                        print("当日价格超过下轨,空单止损,空单损益:{}, 多单入场价格:{}".format(position.position_profit,
                                                                                              quote.last_price))
                    else:
                        print("空单继续持仓")
            if api.is_changing(quote, "datetime"):
                now_time = datetime.strptime(quote.datetime, "%Y-%m-%d %H:%M:%S.%f")
                if now_time.hour == close_hour and now_time.minute == close_minute:
                    target_pos.set_target_volume(0)
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
