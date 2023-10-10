#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'shubin'

from datetime import date

from tqsdk import TqApi, TqSim, TqAuth, TqBacktest, BacktestFinished, TargetPosTask, ta

SYMBOL = ""
back_test_start = date(2022, 1, 1)
back_test_end = date(2022, 1, 1)
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

# Strategy variable
ma_fast_n = 10
ma_slow_n = 40
ma_fast = ta.MA(k_lines, ma_fast_n)
ma_slow = ta.MA(k_lines, ma_slow_n)


def k_line_range(index):
    kline = k_lines.iloc(index)
    return (kline["close"] - kline["low"]) / (kline["high"] - kline["low"])


if __name__ == '__main__':
    try:
        print("策略开始")
        while True:
            api.wait_update()
            if api.is_changing(k_lines, "datetime"):
                # 1. 计算ma
                ma_fast = ta.MA(k_lines, ma_fast_n)
                ma_slow = ta.MA(k_lines, ma_slow_n)

            if api.is_changing(quote, "last_price"):
                # 入场

                if position.pos_short == 0 and position.pos_long == 0:
                    # 前一根K
                    k_line_range_cur = k_line_range(-2)
                    # 后一根K
                    k_line_range_pre = k_line_range(-3)
                    # 多头入场
                    if k_lines[-1].close > ma_fast and k_lines[
                        -1].close > ma_slow and k_line_range_pre < 0.25 and k_line_range_cur > 0.75:
                        target_pos.set_target_volume(5)
                        print("多头入场，入场点为:{}".format(k_lines[-1].close))
                    if k_lines[-1].close < ma_fast and k_lines[
                        -1].close < ma_slow and k_line_range_pre > 0.75 and k_line_range_cur < 0.25:
                        target_pos.set_target_volume(-5)
                        print("空头入场，入场点为:{}".format(k_lines[-1].close))
                # 出场
                # 多头移动止损
                elif position.pos_long > 0:
                    move_stop_loss = min(k_lines[-2].low, k_lines[-3].low) - quote.price_tick
                    if k_lines[-1].close < move_stop_loss:
                        target_pos.set_target_volume(0)
                        print("多头出局，出局价格为:{}".format(k_lines[-1].close))
                    else:
                        print("多头继续持仓，止损价格为:{}".format(move_stop_loss))
                # 空头移动止损
                elif position.pos_short > 0:
                    move_stop_loss = min(k_lines[-2].high, k_lines[-3].high) + quote.price_tick
                    if k_lines[-1].close < move_stop_loss:
                        target_pos.set_target_volume(0)
                        print("空头出局，出局价格为:{}".format(k_lines[-1].close))
                    else:
                        print("空头继续持仓，止损价格为:{}".format(move_stop_loss))


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
