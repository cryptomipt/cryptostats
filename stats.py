import ccxt
import time
import colored

from consts import MIN_BTC_AMOUNT, BASE_TICKERS


def login_all(keys):
    return [login(key) for key in keys]


def login(key):
    exchange = key['Exchange'].lower()
    if exchange not in ccxt.exchanges:
        print('Key {}. Error: Exchange not found'.format(key['Description']))
        return None
    return getattr(ccxt, exchange)({
        'apiKey': key['Key'],
        'secret': key['Secret']
    })


def get_last_buy_order(exchange, symbol):
    try:
        orders = exchange.fetch_closed_orders(symbol=symbol)
        orders = sorted(orders, key=lambda x: x['timestamp'], reverse=True)
        last_buy_order = [
            order for order in orders if order['side'] == 'buy'][0]
    except (ccxt.errors.ExchangeError, IndexError) as e:
        last_buy_order = None

    return last_buy_order


def get_weighted_buy_order(exchange, symbol):
    # TODO: write proper function
    return get_last_buy_order(exchange, symbol)


def get_current_price(exchange, symbol):
    try:
        current_price = float(exchange.fetch_ticker(symbol)['last'])
    except ccxt.errors.ExchangeError as e:
        current_price = 0

    return current_price


def get_portfolio_info(exchange):
    account = exchange.fetch_balance()
    symbols_portfolio_has = []
    symbol_prices = {}
    ticker_btc_amount = {}

    portfolio_btc_size = 0.0

    # fetch symbols_portfolio_has
    # also calculate portfolio_btc_size
    for ticker in account:
        if ticker == "BTC":
            ticker_btc_amount[ticker] = account[ticker]['total']
            portfolio_btc_size += ticker_btc_amount[ticker]
        if ticker.isupper() and account[ticker]['total'] > 0.0:
            for base_ticker in BASE_TICKERS:
                symbol = ticker + '/' + base_ticker

                current_price = get_current_price(exchange, symbol)
                if current_price == 0:
                    continue

                symbol_prices[symbol] = current_price

                if base_ticker == "BTC":  # to calculate every ticker only once
                    ticker_btc_amount[ticker] = account[ticker]['total'] * \
                        current_price
                    portfolio_btc_size += ticker_btc_amount[ticker]

                if account[ticker]['total'] * current_price > MIN_BTC_AMOUNT:
                    symbols_portfolio_has.append(symbol)

    # get portfolio size in btc and usdt
    btc_price = get_current_price(exchange, symbol='BTC/USDT')
    portfolio_info = {
        'portfolio_btc_size': portfolio_btc_size,
        'portfolio_usdt_size': portfolio_btc_size * btc_price,
        'change': []
    }

    for symbol in symbols_portfolio_has:
        symbol_buy_order = get_weighted_buy_order(exchange, symbol)
        if symbol_buy_order is None:
            continue

        symbol_buy_price = float(symbol_buy_order['price'])
        if symbol_buy_price == 0:
            # error or Binance Market buy
            continue

        symbol_buy_ts = float(symbol_buy_order['timestamp'])
        timedelta = time.time() - symbol_buy_ts / 1000
        current_price = symbol_prices[symbol]
        ticker = symbol.split("/")[0]
        ticker_share = ticker_btc_amount[ticker] / portfolio_btc_size

        portfolio_info['change'].append({
            'symbol': symbol,
            'ticker_share': ticker_share,
            'last_buy_price': symbol_buy_price,
            'current_price': current_price,
            'change_percentage': (current_price / symbol_buy_price - 1) * 100,
            'passed_seconds': timedelta
        })

    portfolio_info['change'] = sorted(
        portfolio_info['change'], key=lambda x: x['change_percentage'], reverse=True)
    return portfolio_info


def print_portfolio_info(portfolio_info):
    print(colored.stylize('Total amount: {:.6f} BTC / {:.2f} USDT'.format(
        portfolio_info['portfolio_btc_size'], portfolio_info['portfolio_usdt_size']), colored.fg('yellow')))

    for change_item in portfolio_info['change']:
        change_percentage_color = colored.fg(
            'green') if change_item['change_percentage'] > 0 else colored.fg('red')
        change_percentage_str = colored.stylize('{:.1f}%'.format(change_item['change_percentage']),
                                                change_percentage_color)
        print('{} |\t{}\t| {:.0f} hours passed | {:.1f}% portfolio'.format(
            change_item['symbol'],
            change_percentage_str,
            change_item['passed_seconds'] // 60 // 60,
            change_item["ticker_share"] * 100
        ))
