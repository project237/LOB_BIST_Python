
INPUT_FILE_NAME  = "GARAN.E.csv"
DEBUG_MODE       = 0

from OrderEngine import OrderEngine

def main():
    # ord_engine = OrderEngine(debug_mode=DEBUG_MODE, price_file=MARKET_FILE_NAME, trades_file=TRADES_FILE_NAME)
    ord_engine = OrderEngine(debug_mode=DEBUG_MODE)
    ord_engine.run_with_file(INPUT_FILE_NAME)

if __name__ == '__main__':
    main()