#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'shubin'

from datetime import date

from tqsdk import TqApi, TqSim, TqAuth, TqBacktest, BacktestFinished, TargetPosTask

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

# 策略指标
total_net = 2000000
N = 20


def donchian_channel(k_lines):
    """
    返回唐奇安通道上轨下轨
    :param k_lines:
    :return:
    """
    chanel_top_rail = max(k_lines[-N - 1:]["high"])
    chanel_bottom_rail = min(k_lines[-N - 1:]["low"])
    chanel_mid_rail = (chanel_top_rail + chanel_bottom_rail) / 2
    print("重新计算通道上下轨,上轨:{},中轨:{},下轨:{}".format(chanel_top_rail, chanel_mid_rail, chanel_bottom_rail))
    return chanel_top_rail, chanel_mid_rail, chanel_bottom_rail


def position_unit(k_lines):
    def true_range(k_lines):
        high = k_lines.iloc[-1]["high"]
        low = k_lines.iloc[-1]["low"]
        pre_close = k_lines.iloc[-2]["close"]
        return max(high - low, high - pre_close, pre_close - low)

    # 获取前19日的k_lines
    unit_n = (true_range(k_lines) + sum(map(true_range, [k_lines[-i - 2:-i] for i in range(1, 20)]))) / 20
    unit = (0.01 * total_net) / unit_n
    print("当前计算仓位大小为: {}; 当前计算N 为 {}".format(unit, unit_n))
    return unit, unit_n


top_rail, mid_rail, bottom_rail = donchian_channel(k_lines)
compute_unit, compute_unit_n = position_unit(k_lines)
unit = int(compute_unit)
pre_price = k_lines[-1]["close"]
if __name__ == '__main__':
    try:
        print("策略开始")

        api.wait_update()
        while True:
            if api.is_changing(k_lines, ["high", "low", "datetime"]):
                top_rail, mid_rail, bottom_rail = donchian_channel(k_lines)
                compute_unit, compute_unit_n = position_unit(k_lines)
                unit = int(compute_unit)
            if api.is_changing(quote, "last_price"):
                if position.pos_long == 0 and position.pos_short == 0:
                    # 1. 判断是否建仓
                    if quote.last_price > top_rail and unit > 0:
                        target_pos.set_target_volume(unit)
                        pre_price = quote.last_price
                        print("达到多头入场条件,建立多头仓位,入场价格:{},仓位大小".format(quote.last_price, unit))
                    elif quote.last_price < bottom_rail and unit > 0:
                        target_pos.set_target_volume(-unit)
                        pre_price = quote.last_price
                        print("达到多头入场条件,建立空头仓位,入场价格:{},仓位大小".format(quote.last_price, unit))

                elif position.pos_long > 0:
                    # 1. 是否加仓
                    if quote.last_price > pre_price * 1.5 * compute_unit_n:
                        target_pos.set_target_volume(unit)
                        print("达到多头加仓条件,建立多头仓位,入场价格:{},仓位大小:{}".format(quote.last_price, unit,
                                                                                             position.pos_long))
                        # 2. 是否止盈
                    elif quote.last_price < bottom_rail:
                        target_pos.set_target_volume(0)
                        print("达到多头止盈条件,已实现损益:{}".format(position.position_profit))
                    # 3. 是否止损
                    elif quote.last_price < pre_price * (1 - 2 * compute_unit_n):
                        target_pos.set_target_volume(0)
                        print("达到多头止损条件,已实现损益:{}".format(position.position_profit))
                    # 4. 继续持仓
                    else:
                        print("多头继续持仓,已实现损益:{}".format(position.position_profit))

                elif position.pos_short > 0:
                    # 1. 是否加仓
                    if quote.last_price < pre_price * 1 - 0.5 * compute_unit_n:
                        target_pos.set_target_volume(-unit)
                        print("达到空头加仓条件,建立空头仓位,入场价格:{},仓位大小:{}".format(quote.last_price,
                                                                                             position.pos_short))
                    # 2. 是否止盈
                    elif quote.last_price > top_rail:
                        target_pos.set_target_volume(0)
                        print("达到空头止盈条件,已实现损益:{}".format(position.position_profit))
                    # 3. 是否止损
                    elif quote.last_price < pre_price * (1 + 2 * compute_unit_n):
                        target_pos.set_target_volume(0)
                        print("达到空头止损条件,已实现损益:{}".format(position.position_profit))
                    # 4. 继续持仓
                    else:
                        print("空头继续持仓,已实现损益:{}".format(position.position_profit))


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
