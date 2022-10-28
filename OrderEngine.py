from orders import ActiveOrder, orderA, orderE, orderD
# from OpenOrders import OpenOrders
from pprint import pprint

class OrderEngine:
    def __init__(self):
        self.bids_test = []
        self.asks_test = []
        # self.OpenBids = OpenOrders()
        # self.OpenAsks = OpenOrders()
        self.order_dict = {} # A dict of orderA objects that are not yet fully matched
        # key = order id, value = order object

    def get_order_with_id(self, id):
        return self.order_dict[id]

    def send_order_to_book(self, order, side):
        """
        Called by process_execute_order() when an orderE arrives
        """
        if side == "B":
            # self.OpenBids.insert_order(order)
            self.bids_test.append(order)
        elif side == "S":
            # self.OpenAsks.insert_order(order)
            self.asks_test.append(order)
        else:
            raise ValueError("side must be 'B' or 'S'")
        # TODO - LEFT HERE

    def process_execute_order(self, orderE):
        """
        Called by process_order() when msg_type == "E"
        """
        qty = orderE.qty
        orderA = self.get_order_with_id(orderE.id)
        side = orderA.side

        if orderA.qty == qty:
            # set qty_not_executed to 0
            orderA.qty_not_executed = 0
        elif orderA.qty > qty:
            # set qty_not_executed to qty_not_executed - qty
            orderA.qty_not_executed -= qty
        else:
            raise ValueError("orderE.qty is greater than orderA.qty")
        
        active_order = ActiveOrder(qty, orderA)
        self.send_order_to_book(active_order, side)

    def process_order(self, line):
        """
        Processes a line from the input file and returns ...
        """
        quote_list = line.strip("\n").split(",")

        # raise valueerror if there aren't exactly 9 items in the list
        if len(quote_list) != 9:
            raise ValueError

        keys_list  = ["network_time", "bist_time", "msg_type", "asset_name", "side", "price", "que_loc", "qty", "id"]
        quote_dict = dict(zip(keys_list, quote_list))
        msg_type = quote_dict["msg_type"]

        try:
            # check if msg_type == valid
            assert msg_type in ['A', 'E', 'D']

            # make sure that network_time, bist_time, id are positive integers
            assert quote_dict["network_time"] != "0"
            assert quote_dict["bist_time"]    != "0"
            assert quote_dict["id"]           != "0"

            # =============== ATTRIBUTES FROM ARGS ============== 
            quote_dict["network_time"] = int(quote_dict["network_time"])
            quote_dict["bist_time"]    = int(quote_dict["bist_time"])
            quote_dict["qty"]          = int(quote_dict["qty"])
            quote_dict["price"]        = float(quote_dict["price"])
            quote_dict["que_loc"]      = int(quote_dict["que_loc"])
        except AssertionError:
            raise ValueError

        order = None
        if msg_type == "A":
            order = orderA(**quote_dict)
            self.order_dict[order.id] = order  # adding the order to the order_dict
        elif msg_type == "E":
            order = orderE(quote_dict)
            self.process_execute_order(order)
        elif msg_type == "D":
            order = orderD(quote_dict)

        # TODO - LEFT HERE

    def display(self):
        print("\nPARSED ORDERS:")
        pprint(self.order_dict)
        print("\nASKS:")
        pprint(self.asks_test)
        print("\nBIDS:")
        pprint(self.bids_test)

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)