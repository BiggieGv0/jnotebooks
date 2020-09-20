import pandas as pd
from marketdata import ccomb

def pb_data_loading(Symbol='RTS', TF='bar_timeframe_900'):
    a = ccomb.get_cc_bars(Symbol, TF); 
    a = ([v.start, v.o, v.h, v.l, v.c] for v in a); a = list(a)
    df = pd.DataFrame(a, columns =['TimeStamp', 'O' , 'H', 'L', 'C'])
    return df