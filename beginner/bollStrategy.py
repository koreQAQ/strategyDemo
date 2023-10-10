#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'shubin'

from datetime import date

from tqsdk import TqApi, TqSim, TqAuth, TqBacktest, BacktestFinished, TargetPosTask, ta

SYMBOL = "DCE.i2001"
back_test_start = date(2019, 7, 19)
back_test_end = date(2019, 8, 26)
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
N = 27
p = 2
boll = ta.BOLL(k_lines, N, p)

if __name__ == '__main__':
    try:
        print("策略开始")
        while True:
            api.wait_update()

            # K线结束后才能重新计算
            if api.is_changing(k_lines, "datetime"):
                boll = ta.BOLL(k_lines, N, p)

            # 盘口价格变动
            if api.is_changing(quote, "last_price"):

                # 入场条件
                if position.pos_long == 0 and position.pos_short == 0:
                    if quote.last_price > boll.iloc[-1]["top"]:
                        target_pos.set_target_volume(20)
                        print("多单进场，进场价格:{}".format(quote.last_price))
                    if quote.last_price < boll.iloc[-1]["bottom"]:
                        target_pos.set_target_volume(-20)
                        print("空单进场，进场价格:{}".format(quote.last_price))
                    # 移动止损
                elif position.pos_long > 0:
                    if quote.last_price <= boll.iloc[-1]["mid"]:
                        target_pos.set_target_volume(0)
                        print("多单移动止损，已实现损益:{}".format(position.position_profit))
                    else:
                        print("多单继续持仓, 已实现损益:{}".format(position.position_profit))
                elif position.pos_short > 0:
                    if quote.last_price >= boll.iloc[-1]["mid"]:
                        target_pos.set_target_volume(0)
                        print("空单移动止损，已实现损益:{}".format(position.position_profit))
                    else:
                        print("空单继续持仓, 已实现损益:{}".format(position.position_profit))

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
