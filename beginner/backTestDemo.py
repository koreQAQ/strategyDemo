tq_user =  "shubin"
tq_password = "Lishubin1013"

from tqsdk import TqApi,TqAuth
from datetime import  datetime

if __name__ == '__main__':
    tq_api = TqApi(auth=TqAuth(tq_user, tq_password))
    k_lines = tq_api.get_kline_serial("SHFE.ni2309", 4 * 60 * 60)
    k_line = k_lines.iloc[-1]
    print(datetime.fromtimestamp(k_line["datetime"]/1e9),k_line["open"])
    tq_api.close()