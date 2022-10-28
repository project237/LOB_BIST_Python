from OrderTypes import ActiveOrder, orderA, orderE, orderD
# from OpenOrders import OpenOrders
from pprint import pprint

class OrderEngine:
    def __init__(self):
        self.bids_test_dict     = {}  # list of ActiveOrder objects  
        self.asks_test_dict     = {}  # list of ActiveOrder objects
        self.closed_orders      = []
        # self.OpenBids         = OpenOrders()
        # self.OpenAsks         = OpenOrders()
        self.order_dict         = {} # A dict of orderA objects that are not yet fully matched
        # key = order id, value = order object

    def get_order_with_id(self, id):
        return self.order_dict[id]

    def send_order_to_book(self, order, side):
        """
        Called by process_execute_order() when an orderE arrives
        """
        id = order.id
        if side == "B":
            # self.OpenBids.insert_order(order)
            self.bids_test_dict[id] = order
        elif side == "S":
            # self.OpenAsks.insert_order(order)
            self.asks_test_dict[id] = order
        else:
            raise ValueError("side must be 'B' or 'S'")
        # TODO - LEFT HERE
        # TODO - call remove_order_from_book() if order is matched

    def process_execute_order(self, orderE):
        """
        Called by process_order() when msg_type == "E"
        """
        qty = orderE.qty
        orderA = self.get_order_with_id(orderE.id)
        side = orderA.side

        # if orderA.qty == qty:
        #     # set qty_not_executed to 0
        #     orderA.qty_not_executed = 0
        # elif orderA.qty > qty:
        #     # set qty_not_executed to qty_not_executed - qty
        #     orderA.qty_not_executed -= qty
        # else:
        #     raise ValueError("orderE.qty is greater than orderA.qty")
        # active_order = ActiveOrder(qty, orderA)

        active_order = orderA.process_execute_order(orderE)
        self.send_order_to_book(active_order, side)

    def remove_order_from_book(self, orderA):
        """
        Called from:
        1- process_delete_order() when an orderD arrives
        2- process_execute_order() when an orderE that turns consumed flag of orderA to True
        """
        side = orderA.side
        id   = orderA.id

        # first remove from order_dict
        del self.order_dict[id]

        # then we remove from OpenOrders tree depending on side
        # (for now just remove from the list)
        if side == "B":
            # will remove from OpenOrders tree if it is on the tree
            try:
                del self.bids_test_dict[id]
            except KeyError:
                pass
        elif side == "S":
            # will remove from OpenOrders tree if it is on the tree
            try:
                del self.bids_test_dict[id]
            except KeyError:
                pass
        
        # add to the list of closed orders
        self.closed_orders.append(orderA)

    def process_delete_order(self, orderD):
        id = orderD.id
        orderA = self.get_order_with_id(id)
        orderA.add_to_order_stack(orderD)
        self.remove_order_from_book(orderA)

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
            self.process_delete_order(order)

        # TODO - LEFT HERE

    def display(self):
        # length of order_dict
        print(f"\nACTIVE ORDERS: {len(self.order_dict)} items")
        pprint(self.order_dict)
        # print("\nASKS:")
        # pprint(self.asks_test_dict)
        # print("\nBIDS:")
        # pprint(self.bids_test_dict)
        print(f"\nCLOSED ORDERS: {len(self.closed_orders)} items")
        pprint(self.closed_orders)

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)