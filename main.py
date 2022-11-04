
INPUT_FILE_NAME  = "GARAN.E.csv"
DEBUG_MODE       = 0

from LOB.OrderEngine import OrderEngine

def main():
    ord_engine = OrderEngine(debug_mode=DEBUG_MODE)
    ord_engine.run_with_file(INPUT_FILE_NAME)

if __name__ == '__main__':
    main()
