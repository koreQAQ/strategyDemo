from tqsdk import TqApi, TqAuth
from tqsdk import TqSim, TqKq, TqReplay
from tqsdk import TqBacktest
from tqsdk import TargetPosTask
from datetime import datetime, date

tq_user = "shubin"
tq_password = "Lishubin1013"
tq_auth = TqAuth(tq_user, tq_password)

SYMBOL = "SHFE.ni2309"
N = 14
# 0. 获取行情
tq_api = TqApi(auth=TqAuth(tq_user, tq_password))
# 0.1 模拟账户(本地)
# tq_api = TqApi(TqSim(),auth=tq_auth)
# 0.2 模拟账户(联网)
# tq_api = TqApi(TqKq(),auth=tq_auth)
# 0.3 复盘模式(回放模式)
# tq_api = TqApi(TqSim(), backtest=TqReplay(date(2022, 1, 6)), auth=tq_auth)
# 0.4 回测
tq_api = TqApi(TqSim(),backtest=TqBacktest(start_dt=datetime(2023, 1, 6), end_dt=datetime.now()),auth=tq_auth)
k_lines = tq_api.get_kline_serial(SYMBOL, 60 * 60 * 4, N)
quote = tq_api.get_quote(SYMBOL)
target_pos = TargetPosTask(tq_api, SYMBOL)
position = tq_api.get_position(SYMBOL)
ma = 0
if __name__ == '__main__':
    print("策略开始启动")
    while True:
        tq_api.wait_update()
        # 生成新K线时，重新计算MA
        if tq_api.is_changing(k_lines.iloc[-1], "datetime"):
            ma = sum(k_lines.close[:-1]) / N
            print("移动MA是：", ma)
        # 每次最新价发生变动时，重新进行判断
        if tq_api.is_changing(quote, "last_price"):
            # 开仓策略
            if position.pos_long == 0 and position.pos_short == 0:
                # 如果当前价格上穿ma，开多仓
                if quote.close > ma:
                    print("价格上穿ma，做多")
                    target_pos.set_target_volume(100)
            # 止损策略
            elif quote.close <= ma:
                print("价格下穿ma,平多，")
                target_pos.set_target_volume(0)
