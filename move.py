import streamlit as st
import requests

st.title('Input Move')
st.write('Test input on output price.')
st.write('Currently only for Binance.')
st.write('By: [buklijas.info](http://buklijas.info)')

@st.cache
def get_pairs():
    EI_URL = 'https://api.binance.com/api/v3/exchangeInfo'
    r = requests.get(EI_URL)

    if r.status_code == 200:
        data = r.json()

        trading_pairs = [i['symbol'] for i in data['symbols'] if i['status']=='TRADING']

        return trading_pairs
    else:
        st.write(r.status_code)


col1, col2 = st.beta_columns(2)

with col1:
    option = st.selectbox(
        'Select Pair',
        get_pairs(),
        help='sorted by random')
    st.write('You selected:', option)

with col2:
    amount = float(st.number_input('Input', 1, 10_000_000, 1_000_000, help='amount _ price'))
    st.write(f'Your amount: {amount:_.0f} USDT')

if st.button('Calculate'):
    r = requests.get(f'https://api.binance.com/api/v3/depth?symbol={option}&limit=5000')
    data = r.json()

    total_bids = 0.0
    first_bid_price = float(data['bids'][0][0])
    last_bid_price = float(data['bids'][-1][0])
    #first_bid_price, last_bid_price
    for bids in data['bids']:
        p = float(bids[0]) # price
        q = float(bids[1]) # quantity 
        total = p * q
        total_bids += total
        #p, q, total, total_bids, type(total_bids)

        if total_bids >= amount:
            #st.write('DEBUG', total_bids, amount)
            st.write(f'Input of {amount:_.0f}, will drop price from '
                     f'{first_bid_price:.2f} to {p:.2f} what is {p-first_bid_price:.2f} '
                     f'or {(p/first_bid_price)*100-100:.2f}%')
            break
    else:
        st.write(f'No more BIDS, {first_bid_price} {p} {p-first_bid_price:.2f} {(p/first_bid_price)*100-100:.2f}%')

    total_asks = 0.0
    first_ask_price = float(data['asks'][0][0])
    last_ask_price = float(data['asks'][-1][0])
    #first_ask_price, last_ask_price
    for asks in data['asks']:
        p = float(asks[0]) # price
        q = float(asks[1]) # quantity 

        total = p * q
        total_asks += total

        if total_asks >= amount:
            #st.write('DEBUG', total_asks, amount)
            st.write(f'Input of {amount:_.0f}, will rise price from '
                     f'{first_ask_price:.2f} to {p:.2f} what is {p-first_ask_price:.2f} '
                     f'or {(p/first_ask_price)*100-100:.2f}%')
            break
    else:
        st.write(f'No more ASKS, {first_ask_price} {p} {p-first_ask_price:.2f} {(p/first_ask_price)*100-100:.2f}%')
         
