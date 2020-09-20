def CB(ohlc, moment=0):
    """ ...

    NOTE: ohlc *must* contain spx_C, spx_V, ...;
    """
    ## Alises AMI -> Pandas
    _min_periods = 1
    MA = lambda s, l: pa.rolling_mean(s, l, min_periods=_min_periods)
    LLV = lambda s, l: pa.rolling_min(s, l, min_periods=_min_periods)
    StDev = lambda s, l: pa.rolling_std(s, l, min_periods=_min_periods)
    Ref = lambda series, num: series.shift(-num)
    log = np.log
    Min = lambda *serieses: pa.concat(serieses, axis=1).min(axis=1)
    from pyquant.transforms import RSI as q_RSI, RSI_iter as q_RSI_iter
    RSI = lambda n: q_RSI_iter(ohlc.C, n)
    O, H, L, C, V = ohlc.O, ohlc.H, ohlc.L, ohlc.C, ohlc.V
    # Not recommended to use:
    BBandTop = lambda *ar, **kwa: bbands(*ar, **kwa)[1]
    BBandBot = lambda *ar, **kwa: bbands(*ar, **kwa)[2]
    ADX = lambda n: adx(ohlc, n)

    ## ...
    Upper_Band = BBandTop(C, 5, 1)
    Lower_Band = BBandBot(C, 5, 1)
    b = (C - Lower_Band) / (Upper_Band - Lower_Band)
    ##### НАСТРОЙКИ СКАНЕРА ЦЕНЫ и ЛИКВИДНОСТИ
    ## 1. определение ликвидности бумаги
    ## определение среднего значения V * C у индекса за 65 дней. ВНИМАНИЕ!!! Некотораые поставщики
    ## данных не даеют значение "объем" у индекса
    O, H, L, C, V = ohlc.spx_O, ohlc.spx_H, ohlc.spx_L, ohlc.spx_C, ohlc.spx_V
    VolSP = MA(V * C, 65)  ## SPX'd
    volumeSP = V
    closeSP = C
    O, H, L, C, V = ohlc.O, ohlc.H, ohlc.L, ohlc.C, ohlc.V

    xvolFilter = 3.0 / 1000000  ## пороговое минимальное значение
    Vol_close = MA(C * V, 20)
    liqIndex = Vol_close > (VolSP * xvolFilter) ## SPX'd
    ## 2. определение нижнего порога цены
    minPrice = C > 5
    ## 3. определение верхнего порога цены
    maxPrice = C < 100
    priceLiqScan = liqIndex & minPrice & maxPrice  ## SPX'd
    ##### НАСТРОЙКИ СКАНЕРА СЕТАПА
    ## 1.определение наличия долгосрочного повышательного тренда
    hardLong = C > MA(C, 200)
    ## 2.подтверждение, что тренд развивается
    hardTrend = ADX(5) > 40
    ## 3.подтверждение резкого отката цены
    hardDrop = (BarsSince(b > 0.5) > 3) & (b <= 0.1)
    ## 4.объем не должен быть минимальным
    hardVol = V > LLV(V, 5)
    setupScan = hardLong & hardTrend & hardDrop & hardVol
    ##### ОБЪЕДИНЕНИЕ СКАНЕРОВ
    BuyHR = priceLiqScan & setupScan  ## SPX'd
    ## НАСТРОЙКИ ТРИГГЕРА
    Lmt = 3
    PriceTrigger = Ref(C, -1) * (1.0 - Lmt / 100.0)
    Trigger = (L <= PriceTrigger)

    zero = pa.Series(False, index=O.index)

    ## СОБСТВЕННО ТОРГОВАЯ ЛОГИКА
    Buy = Ref(BuyHR, -1) & Trigger
    ## stB = ValueWhen(Buy, Min(O, PriceTrigger))
    BuyPrice = Min(O, PriceTrigger)
    stp_MA = MA(C, 3)
    sell1 = C > stp_MA
    sell2 = nbarexit(Buy, 5)
    Sell = sell1 | sell2  ##  | (BarsSince(Buy) > 1 & C - stB < 0)
    SellPrice = C
    Short = zero
    Cover = zero
    ## ApplyStop(stopTypeLoss, stopModePercent, 10, 1)
    Short_b = Short; Cover_b = Cover; Buy_b = Buy; Sell_b = Sell

    ## To be processed later with Live Backtest:
    ## maximal price to buy at (via an order, likely)
    BuyLimitPrice = PriceTrigger
    ## limit order signal
    BuyLimit = BuyHR
    ## iterative sell signal
    NBarStop = 5  ## Not implemented yet
    ## Backtest automatic volume
    BT_InitialEquity = 100000
    ## Live-sell
    # X_Sell = sell1  ## NBarStop isn't implemented yet
    X_Sell = sell1 | sell2

    ## NOPE.
    ## It screws up the SigToPos
    # if moment == 1:
    #     Buy = zero
    #     BuyLimit = zero
    ## ...

    ## PyBacktest relevant variables: Buy Sell Short Cover BuyPrice SellPrice
    ## Live Backtest relevant variables: BuyLimitPrice BuyLimit NBarStop X_Sell
    return locals()
