from order import orderA, orderE, orderD
# from OpenOrders import OpenOrders
from pprint import pprint

class OrderEngine:
    def __init__(self):
        # self.OpenBids = OpenOrders()
        # self.OpenAsks = OpenOrders()
        self.order_dict = {}

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
            self.order_dict[order.id] = order
        elif msg_type == "E":
            order = orderE(quote_dict)
        elif msg_type == "D":
            order = orderD(quote_dict)

        pprint(order.__dict__)

        # TODO - LEFT HERE

        

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)