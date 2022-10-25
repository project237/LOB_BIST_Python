
# =================================== PARAMETERS ==================================
INPUT_FILE_NAME = "GARAN.E.csv"

# ==================================== IMPORTS ====================================
from OrderEngine import OrderEngine
from order import order
from pprint import pprint

# ============================== METHODS & EXECUTION ==============================
def process_order(line):
    pass

def main():

    order_engine = OrderEngine()

    with open(INPUT_FILE_NAME, "r") as f:

        for i, l in enumerate(f):

            line = l.split(",")

            try:
                new_order = order(*line)
                order_engine.process_order(new_order)
            except ValueError:
                print(f"Error: Invalid order at line {(i+1)}")
        
    print()
    pprint(order_engine.all_orders)
    pprint(order_engine.active_orders)

if __name__ == '__main__':
    main()