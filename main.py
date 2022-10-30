
# =================================== PARAMETERS ==================================
INPUT_FILE_NAME = "GARAN.E.test2.csv"
DEBUG_MODE      = True

# ==================================== IMPORTS ====================================
from OrderEngine import OrderEngine
# from order import order
from pprint import pprint

# ============================== METHODS & EXECUTION ==============================
def process_order(line):
    pass

def main():
    ord_engine = OrderEngine(debug_mode=DEBUG_MODE)

    with open(INPUT_FILE_NAME, "r") as f:
        for i, l in enumerate(f):
            if DEBUG_MODE: print(f"\nAt Line {i+1}...")

            # terminate if we reach the end of the file
            if l in ["", "\n"] : 
                print("================= END OF FILE REACHED =================\n")
                break
            
            try:
                ord_engine.process_order(l)
            except Exception as e :
                print(f'Error: Invalid order at line {(i+1)} due to \n"{e}"')
                raise e
                
    # ord_engine.display_book()

if __name__ == '__main__':
    main()