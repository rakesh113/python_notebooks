import requests
import json
from requests.structures import CaseInsensitiveDict
import mysql.connector
import datetime as dt
from dateutil import parser
import time

#START_DATE = dt.datetime(2021,4,29,9,16)
#END_DATE = dt.datetime(2021,5,12,15,26)

def get_stockmock_optiondata(ticker, selectedDate, selectedTime):
    url = "https://www.stockmock.in/api/getOC"
    headers = CaseInsensitiveDict()
    headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0"
    headers["Accept"] = "application/json, text/*"
    headers["Accept-Language"] = "en-US,en;q=0.5"
    headers["Accept-Encoding"] = "gzip, deflate, br"
    headers["Content-Type"] = "application/json"
    headers["token"] = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwaG9uZSI6Ijg1NTA4Nzg0MTUiLCJyb2xlIjoiYWRtaW4iLCJjcmVhdGVkT24iOjE2NDE5OTI4OTA3NTZ9.y6NRypwgN2GQgw-aLMc8y4yJ3Ym2lbi2pQBn2gCSXps"
    headers["Origin"] = "https://www.stockmock.in"
    headers["Connection"] = "keep-alive"
    headers["Referer"] = "https://www.stockmock.in/"
    headers["Cookie"] = "_ga_J5S0Y3P2LV=GS1.1.1641992889.44.1.1641994173.0; _ga=GA1.1.1118896481.1624449413; fpestid=gsE4WS7ovKaRMNNBETRWNuSktcNbEvKzswKfbhCEw0Y7LKVfddKHXHT73tWOe3iKnfSdkw; _rdl34hcrd=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJwaG9uZSI6Ijg1NTA4Nzg0MTUiLCJyb2xlIjoiYWRtaW4iLCJjcmVhdGVkT24iOjE2NDE5OTI4OTA3NTZ9.y6NRypwgN2GQgw-aLMc8y4yJ3Ym2lbi2pQBn2gCSXps"
    headers["Sec-Fetch-Dest"] = "empty"
    headers["Sec-Fetch-Mode"] = "cors"
    headers["Sec-Fetch-Site"] = "same-origin"
    headers["TE"] = "trailers"
    
    with open("C:\\Users\\Rakesh\\Documents\\pythons\\application.properties") as f:
        for line in f.readlines():
            if("app.stockmock.api.cookie" in line):
                headers["Cookie"] = "=".join(line.strip().split("=")[1:])
            if("app.stockmock.api.token" in line):
                headers["token"]="=".join(line.strip().split("=")[1:])
                
    data = '{"index":"%s","selectedDate":"%s","selectedTime":"%s"}' % (ticker, selectedDate, selectedTime)
    #data = '{"index":"banknifty","selectedDate":"2021-01-01","selectedTime":"14:50:00"}'
    
    print(data)
    
    resp = requests.post(url, headers=headers, data=data)
    
    if(resp.status_code != 200):
        raise Exception("failed with status: %s, message:%s" % (resp.status_code, resp.json()))
    return resp.json()

def get_zerodha_data(symbol_id, timeframe, startDate, endDate):
    
    #assert(symbol_id)
    #url = "https://kite.zerodha.com/oms/instruments/historical/260105/5minute?user_id=RY1548&oi=1&from=2021-12-16&to=2021-12-17"
    zerodha_url = "https://kite.zerodha.com/oms/instruments/historical/%s/%s?user_id=RY1548&oi=1"
    zerodha_url += "&from=%s&to=%s"
    zerodha_url = zerodha_url % (symbol_id, timeframe, startDate, endDate)
    headers = get_common_headers()
    headers["Referer"] = "https://kite.zerodha.com/chart/web/tvc/INDICES/NIFTY%20BANK/260105"
    headers["authorization"] = "enctoken ahx+GRFYShlJUovwK2PIiJAyXh0BOIO6oY/nMtnyIIWhs1jKc9NnSfuBtktI1vfj/IvK0w7L9k2ho/6mAbO0DGfdmsw/KnkMpSDwc5m+QtDy6GCPcnLi+g=="
    headers["Cookie"] = "_ga=GA1.2.436146067.1602141439; __utma=134287610.436146067.1602141439.1616346921.1616643812.8; __utmc=134287610; public_token=Og97mPTA939Bhef6o5CYAfOUaq8uzj5S; kf_session=VphkXPepyJQwinTxljkJ0jAn08kMRn3b; user_id=RY1548; enctoken=ILGXhKaWGb/TVepXXGe5wsjz/3p8XpL8f3pHWI89mhk1nNSWlrqi4B4dl2/XtW1SjbEXce++5+Db+JMx+/AkUhrjpSY6KrvHx0XPsSw2qJBBxoi0OyOldg=="
    resp = requests.get(zerodha_url, headers=headers)

    print(resp.status_code)
    return resp.json()['data']['candles']

def get_common_headers():
    headers = CaseInsensitiveDict()
    headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0"
    headers["Accept"] = "application/json, text/*"
    headers["Accept-Language"] = "en-US,en;q=0.5"
    headers["Accept-Encoding"] = "gzip, deflate, br"
    headers["Sec-Fetch-Dest"] = "empty"
    headers["Sec-Fetch-Mode"] = "no-cors"
    headers["Sec-Fetch-Site"] = "same-origin"
    headers["TE"] = "trailers"
    headers["Pragma"] = "no-cache"
    headers["Cache-Control"] = "no-cache"
    headers["Connection"] = "keep-alive"
    headers["Content-Type"] = "application/json"
    return headers

def save_zerodha_data_to_db(data_vendor_id, symbol_id, min5_data):
    min5_data = [(1, 1, date_to_str(d[0]),
            d[1], d[2], d[3], d[4], d[5], 0) for d in min5_data]
    # Create the insert strings
    column_str = "data_vendor_id, symbol_id, price_date,open_price, high_price, low_price,\
                    close_price, volume, adj_close_price"
    insert_str = ("%s, " * 9)[:-2]
    final_str = "INSERT INTO min5_price (%s) VALUES (%s)" % (column_str, insert_str)
    #print(final_str)
    with get_db_con() as con:
        cur = con.cursor()
        cur.executemany(final_str, min5_data)
        print("added %d rows to min5_price" % cur.rowcount)
        con.commit()

def save_option_data(data):
    pass

def get_db_con():
    con = mysql.connector.connect(
      host="localhost",
      user="root",
      password="admin",
      database="securities_master"
    )
    return con

def get_bnf_metadata():
    with get_db_con() as con:
        cur = con.cursor()
        cur.execute("SELECT s.id, v.id, s.ticker,vs.vendor_symbol_id FROM vendor_symbol_metadata vs\
                    join symbol s on vs.symbol_id=s.id join data_vendor v on v.id=vs.vendor_id where\
                    v.name = 'Zerodha' and s.ticker='NIFTY BANK'")
        data = cur.fetchall()
    return [{'symbol_id':d[0], 'data_vendor_id':d[1],'ticker':d[2],'vendor_symbol_id': d[3]} for d in data][0]

def fetch_zerodha_data_save_to_db(START_DATE, END_DATE):
    metadata=get_bnf_metadata()
    #START_DATE = '2021-12-24'
    #END_DATE = '2022-01-04'
    END_DATETIME =  parser.parse(END_DATE)

    start_date = parser.parse(START_DATE)
    start_date_str = START_DATE
    end_date = (start_date+ dt.timedelta(days=3))
    end_date_str = end_date.strftime("%Y-%m-%d")
    while(end_date <= END_DATETIME):
        data = get_zerodha_data(metadata['vendor_symbol_id'], '5minute', start_date_str, end_date_str)
        save_data_to_db(metadata['data_vendor_id'], metadata['symbol_id'], data)
        start_date = end_date + dt.timedelta(days=1)
        end_date = (start_date+ dt.timedelta(days=3))
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")


def save_stockmock_data_db(start_date, end_date, end_time, firstCandle = True):
    #START_DATE = dt.datetime(2022,1,3,9,16)
    START_DATE = parser.parse(start_date)
    #END_DATE = dt.datetime(2022,1,4,15,26)
    END_DATE = parser.parse(end_date)
    #END_TIME = dt.time(15,25)
    END_TIME = (parser.parse(end_time)).time()
    
    arr=[]
    retries = 0

    column_str = "data_vendor_id, symbol_id, strikeprice, option_type, expiry,\
                    price_date,close_price, future_price, iv, atm_diff"
    insert_str = ("%s, " * 10)[:-2]
    final_str = "INSERT INTO option_prices (%s) VALUES (%s)" % (column_str, insert_str)

    sdate = START_DATE
    prevsdate = sdate

    while(sdate < END_DATE):
        #time.sleep(0.5)
        #skip if sat or sun
        if(sdate.weekday() > 4):
            sdate = sdate + dt.timedelta(days=1)
            prevsdate = sdate
            continue
        inp_date = sdate.strftime("%Y-%m-%d")
        inp_time = sdate.strftime("%H:%M:%S")
        #print("date:%s, time:%s" % (inp_date, inp_time))
        try:
            resp = get_stockmock_optiondata("banknifty", inp_date, inp_time)
            expiries = resp.keys()
            for expiry in expiries:
                future = float(resp[expiry]['future'])
                for chain in resp[expiry]['chain']:
                    if(abs(int(chain['atmDiff'])) < 500):
                        strike = int(chain['option'][:-2])
                        option_type = chain['option'][-2:]
                        close = float(chain['ltp'])
                        arr.append([2, 1, strike, option_type, expiry, str(sdate), 
                                close, future, float(chain['bsIV']), int(chain['atmDiff'])])
            
            if(sdate.time() >= END_TIME):
                sdate = prevsdate
                sdate = sdate + dt.timedelta(days=1)
                prevsdate = sdate
                firstCandle = True
                if(len(arr) > 0):
                    with get_db_con() as con:
                        cur = con.cursor()
                        cur.executemany(final_str, arr)
                        print("added %d rows to option_prices table, for date:%s" % (cur.rowcount, (sdate.date() + dt.timedelta(days=-1)) ))
                        con.commit()
                        arr = []
                else:
                    print("no data for %s" % (sdate.date() + dt.timedelta(days=-1)))
            else:
                if(firstCandle):
                    sdate = sdate + dt.timedelta(minutes=4)
                    firstCandle = False
                else:
                    sdate = sdate + dt.timedelta(minutes=5)
        except Exception as e:
            print("error occured %s" % e)
            print("data got length:%s" % len(arr))
            #wait for 1 min to avoid too many req
            #if(retries > 15):
            #    print("-------retries exhausted")
            #    break
            time.sleep(15)
            print("=====retrying")
            retries = retries+1
                
    if(len(arr) > 0):
        with get_db_con() as con:
            cur = con.cursor()
            cur.executemany(final_str, arr)
            print("added remaining %d rows to option_prices table for date:%s" % (cur.rowcount, (sdate.date() + dt.timedelta(days=-1)) ))
            con.commit()
            
    print("Fetched and stored data from %s to %s" % (START_DATE, END_DATE))

def add_optiondata_db(arr):
    column_str = "data_vendor_id, symbol_id, strikeprice, option_type, expiry,\
                    price_date,close_price, future_price, iv, atm_diff"
    insert_str = ("%s, " * 10)[:-2]
    final_str = "INSERT INTO option_prices (%s) VALUES (%s)" % (column_str, insert_str)
    with get_db_con() as con:
        cur = con.cursor()
        cur.executemany(final_str, arr)
        print("added remaining %d rows to option_prices table" % cur.rowcount)
        con.commit()
    
def fetch_stockmockdata_on_time():
    START_DATE = dt.datetime(2021,1,1,15,29)
    END_DATE = dt.datetime(2022,1,4,15,29)
    column_str = "data_vendor_id, symbol_id, strikeprice, option_type, expiry,\
                    price_date,close_price, future_price, iv, atm_diff"
    insert_str = ("%s, " * 10)[:-2]
    final_str = "INSERT INTO option_prices (%s) VALUES (%s)" % (column_str, insert_str)

    sdate = START_DATE
    arr = []
    while(sdate <= END_DATE):
        if(sdate.weekday() > 4):
            sdate = sdate + dt.timedelta(days=1)
            continue
        inp_date = sdate.strftime("%Y-%m-%d")
        inp_time = sdate.strftime("%H:%M:%S")
        try:
            resp = get_stockmock_optiondata("banknifty", inp_date, inp_time)
            expiries = resp.keys()
            for expiry in expiries:
                future = float(resp[expiry]['future'])
                for chain in resp[expiry]['chain']:
                    if(abs(int(chain['atmDiff'])) < 500):
                        strike = int(chain['option'][:-2])
                        option_type = chain['option'][-2:]
                        close = float(chain['ltp'])
                        arr.append([2, 1, strike, option_type, expiry, str(sdate), 
                                close, future, float(chain['bsIV']), int(chain['atmDiff'])])
            sdate = sdate + dt.timedelta(days=1)
        except Exception as e:
            print("error occured %s" % e)
            time.sleep(15)
            print("=====retrying")
    with get_db_con() as con:
        cur = con.cursor()
        cur.executemany(final_str, arr)
        con.commit()
        print("added %d rows" % cur.row_count)
 
            
#####     ENTRY point to the file             ###########    
#save_stockmock_data_db("2021-11-29 09:16", "2021-12-31 15:26", "15:25", True)
#fetch_zerodha_data_save_to_db("2022-01-05","2021-01-07")

#fetch_stockmockdata_on_time()
