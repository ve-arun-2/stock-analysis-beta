"""
Chartink screeners the `chartink` source should run.

Maintained by hand — add or remove an entry here to change which screeners
`ChartinkSource` fetches. Nothing else needs to change.

  key    a short friendly label. Stored as `stock_daily_data.source_type` for
         every stock the screener matched, and shown in logs.
  value  the exact "scan clause" for that screener.

How to get the scan clause for one of your saved screeners:
  1. Open the screener on chartink.com and run it.
  2. Open browser DevTools -> Network tab -> click the `process` request.
  3. Under "Payload" / "Form Data", copy the value of `scan_clause`.
     (It is the same text shown in the screener's "Scan" / clause box.)

Example entry (delete or replace):
    "close_above_sma50": (
        "( {cash} ( latest close > latest sma( latest close , 50 ) ) )"
    ),
"""

CHARTINK_SCREENERS: dict[str, str] = { 
    # "your_label": "( {cash} ( ...scan clause... ) )",
    "20-uppercircuit-closed": "( {cash} (  daily close -  1 day ago close /  1 day ago close *  100 >  19.9 and  daily close -  1 day ago close /  1 day ago close *  100 <  20.1 ) )",
    "pattarn-consolidation": "( {57960} (  daily ^7106('source'=' daily close','max_bars'='80','min_bars'='22','pattern_json'='[380,174,212,212,148,225,164,169,159,184,162,138,60,25,20]','match_threshold'='0.15','resample_points'='15','output'='flag_match')^ =  1 and  daily close >  80 and  daily close >  daily ema(  daily close , 200 ) ) )",
    "gradually-closing-price-increasing": "( {cash} (  daily close >  1 day ago close and  1 day ago close >  2 days ago close and  2 days ago close >  3 days ago close and  daily high >=  daily max( 22 ,  daily high ) and  daily close >  100 and  daily count( 5, 1 where  abs(  daily close -  1 day ago close ) /  1 day ago close *  100 <=  15 ) =  5 and  daily volume >  50000 ) )",
    "copy-combined-winners-2434": "( {cash} ( ( {cash} ( ( {cash} (  daily close /  22 days ago close >  1.2 and  market cap >  1000 and  daily close *  daily sma(  daily volume , 20 ) >  30000000 and  daily close >  daily sma(  daily close , 200 ) ) ) ) ) ) )",
    "copy-ankur-s-volume-scan-12130": "( {cash} (  daily volume >  daily sma(  daily volume , 50 ) *  3 and  daily close >  30 and  daily \"close - 1 candle ago close / 1 candle ago close * 100\" >=  7 and  daily sma(  daily volume , 50 ) >=  50000 and  daily volume >  500000 and  daily close >  daily ema(  daily close , 200 ) ) )",
    "50-ema-retracement-with-better-options": "( {cash} (  weekly max( 4 ,  weekly high ) >=  weekly max( 52 ,  weekly high ) and  daily close <=  daily ema(  daily close , 50 ) *  1.05 and  daily close >=  daily ema(  daily close , 50 ) and  daily ema(  daily close , 20 ) >=  daily ema(  daily close , 50 ) and  daily ema(  daily close , 50 ) >=  daily ema(  daily close , 200 ) and  market cap >=  1000 and  daily close >=  100 ) )",
    "52-weeks-high-cross-over": "( {cash} ( ( {cash} (  daily high >=  daily max( 260 ,  daily high ) and  daily close >  daily sma( close,20 ) and  daily rsi( 14 ) >  1 day ago rsi( 14 ) and  daily rsi( 14 ) >  40 and  daily adx di positive( 14 ) >=  daily adx( 14 ) and  daily macd line( 26,12,9 ) >  daily macd signal( 26,12,9 ) and  daily adx( 14 ) >  daily adx di negative( 14 ) and  daily adx di positive( 14 ) >  10 ) ) and  daily close >  40 and  daily volume >  200000 and  daily volume >  1 day ago volume *  2 and  daily close >  1 day ago close and  daily close >  daily open and(  daily high -  daily close ) <=  (  daily high -  daily low ) *  0.3 ) )",
}
