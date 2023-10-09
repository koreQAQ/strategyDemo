#!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'chengzhi'

from datetime import date
from tqsdk import TqApi, TqAuth, TqBacktest, TargetPosTask, BacktestFinished, TqSim

'''
如果当前价格大于5分钟K线的MA15则开多仓
如果小于则平仓
回测从 2018-05-01 到 2018-10-01
'''
acc = TqSim()
# 在创建 api 实例时传入 TqBacktest 就会进入回测模式
api = TqApi(acc, backtest=TqBacktest(start_dt=date(2018, 5, 1), end_dt=date(2018, 10, 1)),
            auth=TqAuth("shubin", "Lishubin1013"))
# 获得 m1901 5分钟K线的引用
klines = api.get_kline_serial("DCE.m1901", 5 * 60, data_length=15)
# 创建 m1901 的目标持仓 task，该 task 负责调整 m1901 的仓位到指定的目标仓位
target_pos = TargetPosTask(api, "DCE.m1901")
try:
    while True:
        api.wait_update()
        if api.is_changing(klines):
            ma = sum(klines.close.iloc[-15:]) / 15
            print("最新价", klines.close.iloc[-1], "MA", ma)
            if klines.close.iloc[-1] > ma:
                print("最新价大于MA: 目标多头5手")
                # 设置目标持仓为多头5手
                target_pos.set_target_volume(5)
            elif klines.close.iloc[-1] < ma:
                print("最新价小于MA: 目标空仓")
                # 设置目标持仓为空仓
                target_pos.set_target_volume(0)
except BacktestFinished as e:
    # 回测结束时会执行这里的代码
    api.close()
    print(acc.trade_log)  # 回测的详细信息

    print(acc.tqsdk_stat)  # 回测时间内账户交易信息统计结果，其中包含以下字段
    # init_balance 起始资金
    # balance 结束资金
    # max_drawdown 最大回撤
    # profit_loss_ratio 盈亏额比例
    # winning_rate 胜率
    # ror 收益率
    # annual_yield 年化收益率
    # sharpe_ratio 年化夏普率
    # tqsdk_punchline 天勤点评
