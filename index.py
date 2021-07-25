import streamlit as st
import pandas as pd
import requests
import concurrent.futures
import threading
import datetime
import calendar


# meni nije jasno, da li ovo mora ovako komplicirano
def date_to_UTC_miliseconds(my_date):
    #current_datetime = datetime.datetime.strptime(my_date, '%d/%m/%Y')

    #d.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    _ = my_date.strftime("%d/%m/%Y")

    current_datetime = datetime.datetime.strptime(_, '%d/%m/%Y')

    current_timetuple = current_datetime.utctimetuple()
    current_timestamp = calendar.timegm(current_timetuple)
    return current_timestamp *1000 # *1000 for miliseconds


thread_local = threading.local()
def get_session():
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session


def get_binance_data(symbol, start_time, symbol_price):    
    # request za cijenu, symbola u odredom datumu
    params = {
        'symbol': symbol,
        'startTime': start_time, 
        'interval': '1d',
        'limit': '1'
    }
    #r = requests.get('https://api.binance.com/api/v3/klines', params=params)
    
    rs = get_session()   # znacajno ubrza, skoro duplo
    r = rs.get('https://api.binance.com/api/v3/klines', params=params)
    
    start_data = r.json()[0]    # [0], jer je lista pa da se uzme prvi
    #print(start_data)
    
    if start_data[0] > start_time:  # open time > start_time
        print(f'for {symbol} open time > start_time {start_data[0]} > {start_time}')
        return symbol

    open_date = start_data[0]
    try:
        open_average_price = float(start_data[7]) / float(start_data[5])
    except ZeroDivisionError:
        print('ZeroDivisionError for', symbol)
        print(start_data)
    else:
        last_price = symbol_price[symbol]
        change = last_price / open_average_price
        return {'symbol': symbol, 'open_date': open_date, 'open_average_price': open_average_price, 'last_price':last_price, 'change': change}
    return None

#
# UI
#

# https://discuss.streamlit.io/t/how-to-access-the-url-and-the-hash-fragments-from-within-the-streamlit-app/1868
    # https://github.com/streamlit/streamlit/issues/1098
        # https://github.com/streamlit/release-demos/blob/master/0.65/demos/query_params.py
get_options = st.experimental_get_query_params()
DEBUG = get_options.get('debug', None)

if DEBUG:
    st.title('Percent diff since today')
    st.write('Select date, press caculate, and wait for few seconds. (using concurrent.futures.ThreadPoolExecutor(max_workers=20) with requests.Session() for HTTP get -> person of good taste)')
    st.write('Takes only USDTsomething or somethingUSDT.')
    st.write(' - assets that are automaticaly removed will be displayed on screen')

st.write('Only for Binance.')
st.write('By: [buklijas.info](http://buklijas.info)')
st.write('')

col1, col2 = st.beta_columns(2)

with col1:
    start_date = st.date_input(
        label='Select start date',
        value=datetime.date(2021, 1, 1),        # default value
        min_value=datetime.date(2017, 1, 1),    # treba vidjeti kada je binance poceo
        max_value=datetime.date.today(),
        help='Select start date fromHelp')
    st.write('You selected:', start_date)

with col2:
    bc = st.button('Calculate')
        
        
if bc:
    st.write('')

    r = requests.get('https://api.binance.com/api/v3/exchangeInfo')
    exchange_info = r.json()

    # it is list because set is not [:10]
    ###trading_symbols = [s['symbol'] for s in exchange_info['symbols'] if s['status'] == 'TRADING']

    # big loop
    trading_symbols = []
    non_trading_symbols = []
    number_of_up_leverage_tokens = 0
    #set_of_up_leverage_tokens = set()
    number_of_down_leverage_tokens = 0
    #set_of_down_leverage_tokens = set()
    assets_to_remove = {'BUSD', 'USDC', 'TUSD', 'SUSD', 'DAI', # Dollar
        'BRL',  # Brazilian real
        'UAH',  # Ukrainian hryvnia
        'AUD',  # Australian dollar
        'RUB',  # Russian ruble
        'GBP',  # Great British Pound 
        'EUR',  # European Union
        'TRY',  # Turkish lira
        
        'IDRT', # Rupiah Token (IDRT) is a stablecoin that is pegged at 1:1 ratio to the InDonesian Rupiah.

        'PAX',  # Paxos Standard (PAX) is a 1:1 USD-collateralized stablecoin approved by the New York State Department of Financial Services (NYDFS). Paxos, as a company, does not charge any extra fees for the issuance and redemption.
        'PAXG', # Pax Gold (PAXG) is a gold-backed cryptocurrency, launched by the creators of Paxos Standard (PAX) in September 2019.

        'BVND', # Binance VND (BVND) is a BEP2 stablecoin pegged to the Vietnamese Dong (VND)
        'BIDR', # Binance IDR (BIDR) is a BEP2 stablecoin pegged 1:1 to the Indonesian Rupiah (IDR)
        
    }
    number_of_symbols = len([s for s in exchange_info['symbols']])
    number_of_traded_symbols = len([s for s in exchange_info['symbols'] if s['status'] == 'TRADING'])
    number_of_non_traded_symbols = len([s for s in exchange_info['symbols'] if s['status'] != 'TRADING'])
    if number_of_traded_symbols + number_of_non_traded_symbols - number_of_symbols:
        st.error(f'number_of_traded_symbols + number_of_non_traded_symbols - number_of_symbols --- {number_of_traded_symbols} + {number_of_non_traded_symbols} - {number_of_symbols}')

    removed_trading_leverage_tokens = []
    removed_non_trading_leverage_tokens = []
    removed_trading_assets = []
    removed_non_trading_assets = []

    for s in exchange_info['symbols']:
        # symbols_assets = {s['baseAsset'], s['quoteAsset']}  # {} is for set()

        # if s['status'] == 'TRADING' and 'USDT' in symbols_assets:
        #     if 'UP' == s['baseAsset'][-2:]:   # jeftin trik zdanja 2 znaka
        #         number_of_up_leverage_tokens += 1
        #         continue   # skip it
        #     elif 'DOWN' == s['baseAsset'][-4:]:
        #         number_of_down_leverage_tokens += 1
        #         continue   # skip it

        #     if assets_to_remove & symbols_assets: # ako ga je pronasao
        #         st.info(f"REMOVED: {s['symbol']}")
        #         continue
        #         pass

        #     # add
        #     trading_symbols.append(s['symbol'])

        symbols_assets = {s['baseAsset'], s['quoteAsset']}  # {} is for set()

        trading = False
        if s['status'] == 'TRADING':
            trading = True

        symbol = s['symbol']

        if 'USDT' in symbols_assets:
            leverage_tokens = False
            if 'UP' == s['baseAsset'][-2:]:   # jeftin trik zdanja 2 znaka
                number_of_up_leverage_tokens += 1
                #continue   # skip it
                leverage_tokens = True
            elif 'DOWN' == s['baseAsset'][-4:]:
                number_of_down_leverage_tokens += 1
                #continue   # skip it
                leverage_tokens = True

            if leverage_tokens:
                if trading:
                    removed_trading_leverage_tokens.append(symbol)
                else:
                    removed_non_trading_leverage_tokens.append(symbol)
                continue

            if assets_to_remove & symbols_assets: # ako ga je pronasao
                #st.info(f"REMOVED: {symbol}")
                if trading:
                    removed_trading_assets.append(symbol)
                else:
                    removed_non_trading_assets.append(symbol)
                continue

            if trading:
                trading_symbols.append(symbol)
            else:
                non_trading_symbols.append(symbol)

    if number_of_up_leverage_tokens != number_of_down_leverage_tokens:
        st.error(f'{number_of_up_leverage_tokens} != {number_of_down_leverage_tokens} --- number_of_up_leverage_tokens != number_of_down_leverage_tokens')

    if DEBUG:
        st.info(f'TRADING symbols {len(trading_symbols)}')          # TRADING
        if removed_trading_leverage_tokens:
            st.info(f' - removed_trading_leverage_tokens {len(removed_trading_leverage_tokens)}, {removed_trading_leverage_tokens}')
        if removed_trading_assets:
            st.info(f' - removed_trading_assets {len(removed_trading_assets)}, {removed_trading_assets}')

        st.info(f'NON TRADING symbols {len(non_trading_symbols)} - {non_trading_symbols}')  # NON TRADING
        if removed_non_trading_leverage_tokens:
            st.info(f' - removed_non_trading_leverage_tokens {len(removed_non_trading_leverage_tokens)}, {removed_non_trading_leverage_tokens}')
        if removed_non_trading_assets:
            st.info(f' - removed_non_trading_assets {len(removed_non_trading_assets)}, {removed_non_trading_assets}')

        st.write(f'Currently there is {len(trading_symbols)} TRADING pairs on Binance.')

    r = requests.get('https://api.binance.com/api/v3/ticker/price')
    org_prices = r.json()

    symbol_price = {}
    for i in org_prices:
        symbol_price[i['symbol']] = float(i['price'])   

    if DEBUG:
        st.write(f'Currently there is {len(symbol_price)} ticker pairs on Binance.')
        
    start_time = date_to_UTC_miliseconds(start_date)

    #print(start_time)
    # 1609459200000 ke 01/01/2021

    data = []
    with st.spinner('Wait for it...'):   

        #data = []
        #start_time1 = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = []

            #for s in trading_symbols[:5]:
            for s in trading_symbols:
                #print(s)
                futures.append(executor.submit(get_binance_data, symbol=s, start_time=start_time, symbol_price=symbol_price))

            symboli_koji_su_stariji_od_start_date = []
            for future in concurrent.futures.as_completed(futures):
                #print('f---', future.result())
                
                fr = future.result()
                if isinstance(fr, dict):
                    data.append(fr)
                elif isinstance(fr, str):
                    #print('DDD')
                    symboli_koji_su_stariji_od_start_date.append(fr)
            
        #duration = time.time() - start_time1
        #duration, data
        
        if DEBUG:
            if symboli_koji_su_stariji_od_start_date:
                st.info(f'symboli_koji_su_stariji_od_start_date: {len(symboli_koji_su_stariji_od_start_date)} {symboli_koji_su_stariji_od_start_date}')
        
        df = pd.DataFrame(data)
        c = sum(df.change)
        average_c = c / len(df.change)

        if DEBUG:
            st.dataframe(df)
            st.write(len(df), 'Change of:', c, 'average:', average_c)
        
        index_percent = (average_c * 100) - 100
        if index_percent > 0:
            index_word = 'increase'
        else:
            index_word = 'decrease'

        btc_change = (df.loc[df['symbol'] == 'BTCUSDT']).iloc[0]['change']
        btc_percent = (btc_change * 100) - 100
        if btc_percent > 0:
            btc_word = 'increase'
        else:
            btc_word = 'decrease'

        init_dollars = len(df)*10.0
        st.markdown(f'In last {(datetime.date.today() - start_date).days} days since {start_date}, inital {init_dollars:,.2f}$ would be {(init_dollars*index_percent)/100:,.2f}$')
        st.write(f'Index {index_word} of {index_percent:.2f}%, Bitcoin {btc_word} of {btc_percent:.2f}%')

        import altair as alt
 
        source = pd.DataFrame({
            ' ': ['Index', 'BitCoin'],
            '% change': [index_percent, btc_percent]
        })

        c = alt.Chart(source).mark_bar().encode(
            x=' ',
            y='% change'
        )

        st.altair_chart(c, use_container_width=True)