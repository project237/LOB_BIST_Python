
# =================================== PARAMETERS ==================================
INPUT_FILE_NAME = "GARAN.E.test.csv"

# ==================================== IMPORTS ====================================
from OrderEngine import OrderEngine
# from order import order
from pprint import pprint

# ============================== METHODS & EXECUTION ==============================
def process_order(line):
    pass

def main():
    ord_engine = OrderEngine()

    with open(INPUT_FILE_NAME, "r") as f:
        for i, l in enumerate(f):
            try:
                ord_engine.process_order(l)
            except Exception as e :
                print(f"Error: Invalid order at line {(i+1)} due to {e}")
                
    ord_engine.display()

if __name__ == '__main__':
    main()