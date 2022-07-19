from bs4 import BeautifulSoup # for html parsing and scraping
import numpy as np # linear algebra
import pandas as pd
import requests
import re
from nsepython import *
from tqdm.auto import tqdm

import logging
import sys
from logging.handlers import TimedRotatingFileHandler

from math import log, sqrt, pi, exp
from scipy.stats import norm


USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"
LANGUAGE = "en-US,en;q=0.5"
EXPIRY_DATE = "28-Oct-2021"

FORMATTER = logging.Formatter("%(asctime)s — %(name)s — %(levelname)s — %(message)s")
LOG_FILE = "tradingapp.log"

def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler

def get_file_handler():
    file_handler = TimedRotatingFileHandler(LOG_FILE, when='midnight')
    file_handler.setFormatter(FORMATTER)
    return file_handler

def get_logger(logger_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG) # better to have too much log than not enough
    logger.addHandler(get_console_handler())
    logger.addHandler(get_file_handler())
    # with this pattern, it's rarely necessary to propagate the error up to parent
    logger.propagate = False
    return logger

After you can create a new logg

#helper functions
def get_riskfreerate():
    bs = get_soup("https://www.rbi.org.in")
    table = bs.find('div',{'id':'wrapper'}).findAll('div')[9].find('table')
    repo_rate_div = table.findAll('tr')[10]
    try:
        str(repo_rate_div).index('91 day T-bills')
    except:
        raise ValueError('91 day T-bills not found, modify search')    
    rate_str = str(repo_rate_div.findChildren()[1])
    rate = re.compile(r'\d+.\d+').search(rate_str).group()
    print("current interrest rate:",rate,"%")
    return float(rate)/100.0

def get_soup(url):
    """Constructs and returns a soup using the HTML content of `url` passed"""
    # initialize a session
    session = requests.Session()
    # set the User-Agent as a regular browser
    session.headers['User-Agent'] = USER_AGENT
    # request for english content (optional)
    session.headers['Accept-Language'] = LANGUAGE
    session.headers['Content-Language'] = LANGUAGE
    # make the request
    html = session.get(url)
    # return the soup
    return BeautifulSoup(html.content, "html.parser")

def get_mc_headers(table):
    """Given a table soup, returns all the headers"""
    headers = []
    for th in table.find("tr").find_all("td"):
        headers.append(th.text.strip())
    return headers

def get_table_rows(table):
    """Given a table, returns all its rows"""
    rows = []
    for tr in table.find_all("tr"):
        cells = []
        # grab all td tags in this table row
        ths = tr.find_all("th")
        if len(ths) > 0:
            cells.append(ths[0].text.strip())
        tds = tr.find_all("td")
        if len(tds) == 0:
            # if no td tags, search for th tags
            # can be found especially in wikipedia tables below the table
            ths = tr.find_all("th")
            for th in ths:
                cells.append(th.text.strip())
        else:
            # use regular td tags
            for td in tds:
                cells.append(td.text.strip())
        rows.append(cells)
    return rows

def get_arbitrage_scripts():
    bs = get_soup('https://www.moneycontrol.com/stocks/fno/marketstats/arbitrage/futures-spot-near.html')
    headers = get_mc_headers(bs.find('div', {'class':'tbheadnn'}).find('table'))
    rows = get_table_rows(bs.find('div',{'id':'datatab_1'}))
    #print("headers:",headers)
    df = pd.DataFrame(rows, columns=headers)
    #print(df.head(2))
    df['Spot'] = df['Spot'].apply(lambda x:float(x.replace(',','')))
    df['Future'] = df['Future'].apply(lambda x:float(x.replace(',','')))
    return df
    
def d1(S,K,T,r,sigma):
    return np.divide((log(S/K)+(r+sigma**2/2.)*T), (sigma*sqrt(T)))
def d2(S,K,T,r,sigma):
    return d1(S,K,T,r,sigma)-sigma*sqrt(T)

def filterNan(x):
    if np.isnan(x):
        return 0
    else:
        return x

def call_premium(S,K,T,r,sigma):
    price = S*norm.cdf(d1(S,K,T,r,sigma))-K*exp(-r*T)*norm.cdf(d2(S,K,T,r,sigma))
    res = {'price':round(filterNan(price),2),
           'delta':filterNan(delta(S,K,T,r,sigma,'c')), 
           'gamma':filterNan(gamma(S,K,T,r,sigma)), 
           'vega':filterNan(vega(S,K,T,r,sigma)), 
           'theta':filterNan(theta(S,K,T,r,sigma,'c')), 
           'rho':filterNan(rho(S,K,T,r,sigma,'c'))
          }
    return res

def put_premium(S,K,T,r,sigma):
    price = K*exp(-r*T)-S+call_premium(S,K,T,r,sigma)['price']
    res = {'price':round(filterNan(price),2),
           'delta':filterNan(delta(S,K,T,r,sigma,'p')), 
           'gamma':filterNan(gamma(S,K,T,r,sigma)), 
           'vega':filterNan(vega(S,K,T,r,sigma)), 
           'theta':filterNan(theta(S,K,T,r,sigma,'p')), 
           'rho':filterNan(rho(S,K,T,r,sigma,'p'))
          }
    return res

def FuturePrice(spotPrice, benefit, cost, r, t):
    price = (spotPrice - benefit + cost)*math.pow(1 + r, t)
    res = {'price':round(filterNan(price),2),
           'delta':1, 
           'gamma':0, 
           'vega':0, 
           'theta':0, 
           'rho':0
          }
    return res

def FuturePriceV2(S, d, rf, t):
    price = S * (1+ rf*(t/365.0)) - d
    res = {'price':round(filterNan(price),2),
           'delta':1, 
           'gamma':0, 
           'vega':0, 
           'theta':0, 
           'rho':0
          }
    return res

def delta(S,K,T,r,sigma,cp):
    if(cp == 'c'):
        return norm.cdf(d1(S,K,T,r,sigma))
    else:
        return -norm.cdf(-d1(S,K,T,r,sigma))
def gamma(S,K,T,r,sigma, cp = 'c'):
    return norm.pdf(d1(S,K,T,r,sigma))/(S*sigma*sqrt(T))
def vega(S,K,T,r,sigma, cp = 'c'):
    return 0.01*(S*norm.pdf(d1(S,K,T,r,sigma))*sqrt(T))
def theta(S,K,T,r,sigma, cp):
    if(cp == 'c'):
        return 0.01*(-(S*norm.pdf(d1(S,K,T,r,sigma))*sigma)/(2*sqrt(T)) - r*K*exp(-r*T)*norm.cdf(d2(S,K,T,r,sigma)))
    else:
        return 0.01*(-(S*norm.pdf(d1(S,K,T,r,sigma))*sigma)/(2*sqrt(T)) + r*K*exp(-r*T)*norm.cdf(-d2(S,K,T,r,sigma)))
def rho(S,K,T,r,sigma, cp):
    if(cp == 'c'):
        return 0.01*(K*T*exp(-r*T)*norm.cdf(d2(S,K,T,r,sigma)))
    else:
        return 0.01*(-K*T*exp(-r*T)*norm.cdf(-d2(S,K,T,r,sigma)))

def read_optionchainData(res, spot, expiry_date, company = ""):
    oc_data = res['records']['data']
    assert(len(oc_data) >= 2)
    #diff = get_options_strike_diff(res)
    itm_strikes = get_ITM_strikes(res, spot)
    #print("company:",company, "itms", itm_strikes)
    data = []
    for x in oc_data:
        if(x['expiryDate'] == expiry_date and x['strikePrice'] in itm_strikes):
            alldata = {}
            try:
                ce_price = x['CE']['lastPrice']
                pe_price = x['PE']['lastPrice']
                minVol = min(x['CE']['totalTradedVolume'], x['PE']['totalTradedVolume'])
                data.append([ce_price,pe_price,x['CE']['impliedVolatility'], x['PE']['impliedVolatility'],
                            x['CE']['totalTradedVolume'], x['PE']['totalTradedVolume'], minVol, x['strikePrice']])
            except Exception as e:
                print("exception",e, "strike", x['strikePrice'],"company:",company)
                pass
    df = pd.DataFrame(data, columns = ['CE','PE','civ','piv','callvol','putvol', 'minVol', 'strike'])
    return df.loc[(df.CE != 0) & (df.PE != 0)].set_index('strike')
    #return df.loc[(df.CE != 0) & (df.PE != 0) & (df.civ != 0) & df.piv != 0]

def get_options_strike_diff(dat):
    oc_data = dat['records']['data']
    tmp = {}
    for x in oc_data:
        tmp[x['strikePrice']] = 0
    keyList = list(tmp.keys())
    keyList.sort()
    return keyList[1]-keyList[0]

def get_ITM_strikes(dat, spot):
    strikes = [i['strikePrice'] for i in dat['records']['data']]
    strikes.sort()
    itm = 0
    for i in range(len(strikes)):
        if(strikes[i] > spot):
            itm = i
            break
    return [strikes[itm-1],strikes[itm]]

def enrich_order_data(company, spot, priceDf, future_market_prem, risk_free_rate, lotSize):
    time_to_expiration = 0.0
    profits = []
    for df in priceDf.itertuples():
        strike = df[0]
        call_expiry_prem = min(spot - strike, 0)
        put_expiry_prem = min(strike - spot, 0)
        profit = round(((call_expiry_prem - df[1]) +(0 - put_expiry_prem + df[2]) + (future_market_prem - spot))*lotSize, 2)
        #print("strike",strike,"call=",df[1],"put=",df[2], "future=",future_market_prem)
        profits.append(profit)
    priceDf['profit'] = profits
    priceDf['future_price'] = [future_market_prem] * len(priceDf)
    priceDf['script'] = [company] * len(priceDf)
    priceDf['lot_size'] = [lotSize] * len(priceDf)
    #priceDf.rename(columns={'CE':'','PE':''}
    return priceDf

def get_maximum_profit_strike(res, option_price, future_market_prem, risk_free_rate, lotSize):
    inp = [x['strikePrice'] for x in res['records']['data']] 
    time_to_expiration = 0/365.0
    future_expiry = 0.0
    best_pl = {'strike':0,'profit':0}
    for i in range(0,len(option_price)):
        #print(option_price['CE'].iloc[i])
        call_market_prem = option_price['CE'].iloc[i]
        put_market_prem = option_price['PE'].iloc[i]
        call_iv = (option_price['civ'].iloc[i])/100.0
        put_iv = (option_price['piv'].iloc[i])/100.0
        if(call_market_prem <=0 or put_market_prem <=0):
            continue
        strike_price = option_price.index[i]
        #print("strike",strike_price,"call=",call_market_prem,"put=",put_market_prem, "future=",future_market_prem)
        call_prices = [call_premium(x, strike_price, time_to_expiration, risk_free_rate, call_iv)['price'] - call_market_prem for x in inp]
        put_prices = [put_market_prem - put_premium(x, strike_price, time_to_expiration, risk_free_rate, put_iv)['price'] for x in inp]
        future_prices = [future_market_prem - FuturePrice(x, 0, 0, risk_free_rate, future_expiry)['price'] for x in inp]
        result = [round(call_prices[x]+put_prices[x]+future_prices[x],2) for x in range(0,len(inp))]
        #print("Profit=",(result[0] * lotSize))
        if(result[0] > best_pl['profit']):
            best_pl['strike'] = strike_price
            best_pl['profit'] = result[0]
    return best_pl

def fetch_latest_prices(strike, script):
    result = {'strike':strike, 'script':script}
    data = nse_fno(script)
    for s in data['stocks']:
        if(s['metadata']['instrumentType'] == 'Stock Futures' and s['metadata']['expiryDate'] == '28-Oct-2021'):
            result['future_price'] = s['metadata']['lastPrice']
        if(s['metadata']['instrumentType'] == 'Stock Options' and s['metadata']['expiryDate'] == '28-Oct-2021'):
            if(s['metadata']['strikePrice'] == strike):
                if(s['metadata']['optionType'] == 'Call' and s['metadata']['lastPrice'] != 0):
                    result['call_price'] = s['metadata']['lastPrice']
                elif(s['metadata']['optionType'] == 'Put' and s['metadata']['lastPrice'] != 0):
                    result['put_price'] = s['metadata']['lastPrice']
    return result

def cal_pnl(script, strike, callPrice, putPrice, futurePrice, lotSize):
    inp = [{'strike':strike,'script':script,'call_price':callPrice,
           'put_price':putPrice,'future_price':futurePrice,'lot_size':lotSize}]
    return cal_pnlV2(inp)
    
##param:orders of type [{'strike':100,'script':'asd','call_price':10,'put_price':9,'future_price':105,'lot_size':10}] 
def cal_pnlV2(orders):
    totalPnL = 0
    for order in orders:
        curr = fetch_latest_prices(order['strike'], order['script'])
        print("#"*50)
        profit = (0 - order['future_price'] + curr['future_price'] + order['call_price'] - curr['call_price']
                    - order['put_price'] + curr['put_price']) * order['lot_size']
        print("Company:",order['script'], " Profit:", profit)
        totalPnL += profit
    print("*"*50)
    print("Total profit of portfolio:", totalPnL)
    return

def getScriptsAndPlaceOrders(): 
    risk_free_rate = get_riskfreerate()
    all_arbitrage_scrips = get_arbitrage_scripts()
    MAX_SCRIPTS = len(all_arbitrage_scrips) - 1
    MAX_SCRIPTS = 50
    shortlisted_scrips = all_arbitrage_scrips[:MAX_SCRIPTS]
    orders = []
    minVols = []
    option_price_list = []
    for i in tqdm(range(MAX_SCRIPTS)):
        #print("#"*40)
        script = all_arbitrage_scrips.iloc[i]
        #print("Company:",script['Company'])
        res = nse_optionchain_scrapper(script['Company']) 
        spot = script.Spot
        future_market_prem = script.Future
        option_price = read_optionchainData(res, spot, EXPIRY_DATE, script['Company'])
        time_to_expiry = 0/365.0
        lotSize = int(script["Lot Size"])
        
        option_price = enrich_order_data(script['Company'], spot, option_price, future_market_prem, risk_free_rate, lotSize)
        option_price.reset_index(inplace=True)
        option_price_list.append(option_price)
#     ordersDf = pd.DataFrame(orders, columns = ['script','strike','call_price','put_price','call_vol',
#                                               'put_vol','future_price','lot_size','max_pnl','minVol'])
    ordersDf = pd.concat(option_price_list)
    ordersDf = ordersDf.sort_values(by = ['minVol'], ascending = False)[:30]
    ordersDf = ordersDf.sort_values(by = ['profit'], ascending = False)[:5]
    ordersDf['profit_pips'] = round(ordersDf['profit']/ordersDf['lot_size'],2)
    print(ordersDf[['script','CE','PE','future_price','profit','profit_pips']])
    #print("Max profit=",pnl['profit']*lotSize, "strikeprice=",pnl['strike'])
    return ordersDf

def get_margin(script, strike, lotSize):
    params = {
        "action":'calculate',
        "exchange[]":['NFO','NFO','NFO'],
        "product[]":['FUT','OPT','OPT'],
        "scrip[]":[],
        "option_type[]":['CE','CE','PE'],
        "strike_price[]":[''],
        "qty[]":[],
        "trade[]":['sell','buy','sell']
    }
    
    params["scrip[]"] += [script+"21OCT"]*3
    params["strike_price[]"] += [strike] * 2 
    params["qty[]"] += [lotSize] * 3

    head = {
            "User-Agent": USER_AGENT,
            "X-Requested-With": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01"
        }

    res = requests.post("https://zerodha.com/margin-calculator/SPAN",data = params, headers = head)
    prem = 0
    try:
        prem = res.json()['total']['total']
    except Exception as e:
        print(e, "response:",res.json())
    return prem

####Classes that can be used to create,process orders
class Basket:
    def __init__(self, company, strike, fut, call, put, lot, maxProfit = 0.0):
        self.company = company
        self.strike = strike
        self.fut = fut
        self.call = call
        self.put = put
        self.lot_size = lot
        self.curr_fut = 0.0
        self.curr_call = 0.0
        self.curr_put = 0.0
        self.premium = 1
        self.profit = 0.0
        self.percent_profit = 0.0
        self.mtm = 0.0
        self.max_profit = maxProfit
        self.expected_returns = 0.0
        
    def cal_profit(self):
        curr = fetch_latest_prices(self.strike, self.company)
        self.curr_fut = curr['future_price']
        self.curr_call = curr['call_price']
        self.curr_put = curr['put_price']
        profit = (self.fut - self.curr_fut - self.call + self.curr_call
                    + self.put - self.curr_put) * self.lot_size
        if self.premium <= 1:
            self.premium = round(get_margin(self.company, self.strike, self.lot_size),2)
        self.expected_returns = (profit / self.premium) * 100
        self.mtm = round(profit, 2)
        print("Company:",self.company, " Profit:", profit, "investedamount:", self.premium,"%returns:", self.expected_returns)
        
class OrderBook:
    def __init__(self):
        self.Orders = []
    
    def add_ordersV2(self, orders):
        for o in orders:
            self.Orders.append(Basket(o['script'], o['strike'], o['future_price'], o['call_price'], 
                                o['put_price'], o['lot_size'],o['max_pnl']))
    def add_orders(self, ordersDf):
#         order of clumns in Dataframe ['CE','PE','civ','piv','callvol','putvol', 'minVol', 
#                                        'strike','profit','future_price','script','lot_size']
#         basket params:[company, strike, fut, call, put, lot, maxProfit]
        for o in range(len(ordersDf)):
            self.Orders.append(Basket(ordersDf['script'].iloc[o], ordersDf['strike'].iloc[o], ordersDf['future_price'].iloc[o],
                                      ordersDf['CE'].iloc[o], ordersDf['PE'].iloc[o], ordersDf['lot_size'].iloc[o],
                                      ordersDf['profit'].iloc[o]))

    def cal_profits(self):
        totalpnl = 0.0
        totalprem = 0.0
        print("#"*30, "Profits", "#"*30)
        for o in self.Orders:
            o.cal_profit()
            totalpnl += o.mtm
            totalprem += o.premium
        returns = round((totalpnl/totalprem)*100, 2)
        print(" "*20, "Net Profit:", totalpnl, "%returns:", returns)