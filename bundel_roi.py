import streamlit as st
import pandas as pd
import requests
import concurrent.futures
import threading
import datetime
import calendar

# https://discuss.streamlit.io/t/how-to-access-the-url-and-the-hash-fragments-from-within-the-streamlit-app/1868
    # https://github.com/streamlit/streamlit/issues/1098
        # https://github.com/streamlit/release-demos/blob/master/0.65/demos/query_params.py
get_options = st.experimental_get_query_params()
DEBUG = get_options.get('debug', None)

#
# UI
#
st.write('By: [buklijas.info](http://buklijas.info)')
#st.write('')
uploaded_file = st.file_uploader('Your Bundel File', type='.json', help='Help tool tip test')
st.write('')

if uploaded_file is not None:
    _ = uploaded_file.name.split('_')[0]
    bundle_date = datetime.datetime.strptime(_, "%Y%m%d").date()

    df = pd.read_json(uploaded_file)

    r = requests.get('https://api.binance.com/api/v3/ticker/price')
    org_prices = r.json()

    symbol_price = {}
    for i in org_prices:
        symbol_price[i['symbol']] = float(i['price'])   

    def get_current_price(x):
        return symbol_price[x]

    df['last_price'] = df['symbol'].apply(get_current_price)
    df['value'] = df['origQty'] * df['last_price']
    df['diff_$'] = df.value - df.cummulativeQuoteQty
    df['diff_%'] = (df.value / df.cummulativeQuoteQty) * 100 - 100

    org = sum(df.cummulativeQuoteQty)
    now = sum(df.value)
    diff = now - org
    diff_p = (now / org) * 100 - 100
    age_in_days = (datetime.date.today() - bundle_date).days
    # https://www.investopedia.com/terms/c/cagr.asp, Compound Annual Growth Rate 
    if age_in_days != 0:    # if you are checking same day
        cagr = (now / org) ** (1/(age_in_days/365))
    else:
        cagr = 0.0

    st.write(f'From {bundle_date} in {org:.2f}, now {now:.2f} after {age_in_days} days --- diff {diff:.2f}$, {diff_p:.2f}%')
    st.write(f'Compound Annual Growth Rate {cagr:.2f}%')
    
    number_of_assets = len(df)
    asset_in_plus = len(df[df['diff_$'] >= 0.0])
    asser_in_minus = len(df[df['diff_$'] < 0.0])
    liquidate = sum(df[df['value'] >= 10.0]['value'])
    non_liquid_value = sum(df[df['value'] < 10.0]['value'])
    

    #st.write(f'{number_of_assets=} {asset_in_plus=} {asser_in_minus=} {liquidate=:.2f}$ --- liquidated_diff {liquidate-org:.2f}$')

    st.write(f'Assets {number_of_assets} = {asset_in_plus} / ({asser_in_minus})')
    st.write(f'Can sell {liquidate:.2f}$ --- sell diff {liquidate-org:.2f}$ --- less than 10$ sum {non_liquid_value:.2f}$')

    # show df
    columns_to_ignore = ['orderId', 'orderListId', 'clientOrderId', 'price', 'executedQty', 'status', 'timeInForce', 'type', 'side', 'fills_commissionAsset',' tradeId', 'fills', 'fills_tradeId']
    st.write(df.loc[:, ~df.columns.isin(columns_to_ignore)])

    # izracunati po danima, graf

