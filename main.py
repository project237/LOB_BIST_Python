INPUT_FILE_NAME  = "GARAN.E.mini.csv"
DEBUG_MODE       = 0
CONCURRENT_MODE  = 0

from LOB.OrderEngine import OrderEngine

def main():
    # ord_engine = OrderEngine(debug_mode=DEBUG_MODE)
    ord_engine = OrderEngine(debug_mode=DEBUG_MODE, concurrent_mode=CONCURRENT_MODE, price_file="market_data.mini.csv", trades_file="trades.mini.csv", order_book_file="LOB.mini.txt", orderA_file="closed_orders.mini.txt", lob_file="LOB.mini.csv")
    ord_engine.run_with_file(INPUT_FILE_NAME)

if __name__ == '__main__':
    main()
