
# =================================== PARAMETERS ==================================
# INPUT_FILE_NAME  = "GARAN.E.test2.csv"
INPUT_FILE_NAME  = "GARAN.E.csv"
OUTPUT_FILE_NAME = "market_data.csv"
DEBUG_MODE       = 0

# ==================================== IMPORTS ====================================
from OrderEngine import OrderEngine, InvalidOrder
# from order import order
from pprint import pprint

# ============================== METHODS & EXECUTION ==============================

def main():
    ord_engine = OrderEngine(debug_mode=DEBUG_MODE, price_file=OUTPUT_FILE_NAME)

    with open(INPUT_FILE_NAME, "r") as f:
        for i, l in enumerate(f):
            if DEBUG_MODE: 
                print(f"\n ============================================= At Line {i+1} =============================================")
                if i == 30000: 
                    print("DEBUG MODE: FINISHED")
                    break
            elif i % 1000 == 0:
                print(f"\n ============================================= At Line {i+1} =============================================")

            # terminate if we reach the end of the file
            if l in ["", "\n"] : 
                print("================= END OF FILE REACHED =================\n")
                break
            
            try:
                ord_engine.process_order(l)
            except InvalidOrder as e:
                 # This error doesn't raise any exception, so we ignore the invalid order and process the next one
                print(f'\nInvalid order at line {(i+1)} due to \n==> {e}')
            except Exception as e :
                print(f'\nError: "{e}" at line {(i+1)}')
                print("\nPrinting Order Book and exiting...")
                ord_engine.display_book()
                raise e
    
    if not DEBUG_MODE: ord_engine.display_book()

if __name__ == '__main__':
    main()