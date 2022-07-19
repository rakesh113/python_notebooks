from RUtils import *
import time
import datetime

EXPIRY_DATE = "28-Oct-2021"

book = OrderBook()
today = datetime.datetime.now()
market_end = datetime.datetime(today.year, today.month, today.day, 15, 20)

logger = get_logger("ArbitrageRunner")

def getProps():
    props = {}
    try:
        with open('application.properties') as propsFile:
            for line in propsFile.readlines():
                arr = line.split('=')
                props[arr[0].strip()] = arr[1].strip()
    except IOError:
        logger.error("Properties file doesn't exist")
    
    return props

orderHash = {}

while today < market_end:
    logger.info("starting new arb opportunities search")
    start = datetime.datetime.now()
    arb_scripts = getScriptsAndPlaceOrders()
    new_scripts = []
    for s in arb_scripts:
        if s['script']+s['strike'] not in orderHash:
            new_scripts.append(s)
    book.add_orders(new_scripts)
    props = getProps()
    if props['app.arbitrage.checkprofits'] == 'True':
        logger.info("getting propfits on current orders")
        book.cal_profits()
    today = datetime.datetime.now()
    logger.info("ended arb opportunities search")
    time.sleep(5*60 - (today - start).seconds + 1)
    
