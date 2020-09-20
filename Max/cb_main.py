
#!/usr/bin/enb python
# coding: utf8

from pystratutils.nbhelpers import *

exec open('cb_func.py').read()

def main(_sym='AAPL', _run_vec=False, run_ibt=False, _eod_time=(15, 55)):
    #### Data

    ### Daily
    start = datetime.date(1998, 1, 1)
    ohlc_full_b = marketdata.ext.load_metotron(_sym)
    ohlc_full_b = ohlc_full_b.ix[start:]
    spx_full_b_b = marketdata.ext.load_metotron('$SPX')
    ohlc_full_b = add_other_ohlc(ohlc_full_b, spx_full_b_b, 'spx_', dropna=True)

    # spx_full_b = spx_full_b_b.reindex(ohlc_full_b.index, method='ffill')
    # spx = spx.ix[start:]
    # print venn(ohlc.index, spx.index)[1:]
    # ohlc, spx = intersect_index(ohlc, spx)
    # print venn(ohlc.index, spx.index)[1:]

    ### Intraday
    ohlc_id = marketdata.ext.load_iqfdl1('AAPL_60')
    # spx_id = marketdata.ext.load_iqfdl1('SPXS_60')  ## NOPE.
    # spx_id_daily = ohlcv_resample(spx_id, 'D')
    ## Construt some mockup from the other data:
    ## TODO: chunk ohlc_id into daily-ish bars from 00:00 to 15:00
    ohlc_id_daily = ohlcv_resample(ohlc_id, 'D')
    ## XXXX: hax: account for dissolution of stocks
    _quotient = None
    for i in xrange(10):
        _day1 = ohlc_id_daily.iloc[i]
        _day1ts = _day1.name
        try:
            _day1base = ohlc_full_b.ix[_day1ts]
        except KeyError:
            continue
        _quotient1 = _day1['O'] / _day1base['O']
        if _quotient is None:
            _quotient = _quotient1
        else:
            ## Average them out
            # _quotient = (_quotient * i + _quotient1) / (i + 1)
            ## Same as:
            _quotient = _quotient - _quotient / (i + 1) + _quotient1 / (i + 1)
    if _quotient is None:
        raise Exception("Could not figure out the dissolution quotient")
    ## XXXX: even more dubious: rounding of the quotient
    if abs(_quotient - int(_quotient)) > 0.01:
        raise Exception("Suspiciously non-round quotient: %r" % (_quotient,))
    _quotient = float(int(_quotient))

    print "Applying id-bars quotient: %0.4f" % (_quotient,)
    for k in 'O H L C'.split():
        ohlc_id[k] = ohlc_id[k] / _quotient
        ohlc_id_daily[k] = ohlc_id_daily[k] / _quotient

    ## XXXX: hax: we don't have the proper intraday data for the spx, so
    ## put in some other data (backward-causal!) of it
    ohlc_id_daily = add_other_ohlc(ohlc_id_daily, spx_full_b_b, 'spx_', dropna=True)


    ### EOD
    ohlc_eod_bars, ohlc_eod_prices = chunk_id(ohlc_id, _eod_time)
    #spx_eod_bars, _ = chunk_id(spx_id, _eod_time)
    ## HAX: take the previous day SPX
    spx_eod_bars = spx_full_b_b.shift(1)
    ohlc_eod_bars = add_other_ohlc(ohlc_eod_bars, spx_eod_bars, 'spx_', dropna=True)

    # spx_full_x = spx_full_b_b.reindex(ohlc_eod_bars.index, method='ffill')

    #### Backtest

    ### Vectored

    if _run_vec:
        loc_base = CB(ohlc_full_b)
        loc_df_base = loc2df(loc_base)

        stp_base = SigToPos(mkvol=lambda *ar, **kwa: 1, init_equity=0)
        poss_base, meta_base = stp_base.signals_to_positions(loc_df_base, ohlc_full_b)
        poss_base['symbol'] = _sym
        poss_base.to_csv('/home/data/tmp/cb_trades_py1_%s.csv' % (_sym,), index_label='timestamp')
        print "vectored position changes: ", len(poss_base)

    ### Iterative
    ibt = IterBacktest(
        CB,
        ohlc_full_b.ix['2007-04-27':'2013-05-27'],
        id_bars=ohlc_eod_bars, id_prices=ohlc_eod_prices,
        min_bars=1, max_steps=100000)

    if run_ibt:
        ibt_res = ibt.run()

        ibt_res.to_csv('/home/data/tmp/cb_trades_py_it_%s.csv' % (_sym,), index_label='timestamp')

    return locals()



if __name__ == '__main__':
    try:
        res = main()
    except Exception:
        import ipdb
        _, _, sys.last_traceback = sys.exc_info()
        import traceback
        traceback.print_exc()
        ipdb.pm()
    locals().update(res)
