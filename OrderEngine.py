
import sys
from io import StringIO
from OrderTypes import orderA, orderE, orderD
# from OpenOrders import OpenOrders
from OrderTree import OrderTree
from pprint import pprint, pformat

class OrderEngine:
    """
    todo - remove bids_test_dict and asks_test_dict when tests are done
    ASSUMPTION:
    1- An order A cannot receive an orderE and orderD at different times
    """
    def __init__(self, debug_mode=False, price_file=None):
        self.debug_mode          = debug_mode # if True, prints the order book, closed_orderAs and active_orderAs after processing each order
        self.price_file          = price_file # file name where the market info will be recorded
        self.bids_test_dict      = {}  # list of active orderAs on the side of Bids  
        self.asks_test_dict      = {}  # list of active orderAs on the side of Asks
        self.OpenBids            = OrderTree()
        self.OpenAsks            = OrderTree()
        self.trades              = [] # A list of trades that have been matched
        self.closed_orderAs      = [] # List of orderA's that have been fully matched or canlceled, which esentially contains other orders
        self.active_orderAs      = {} # A dict of orderA objects that are not yet fully matched, key = order id, value = order object
        self.time_series         = [] # A list of dicts, each dict contains the order book at a specific time

        # add columns to the price file if a file name is provided
        if self.price_file is not None:
            with open(self.price_file, 'w') as f:
                f.write("bist_time,ask,bid,volume\n")

    def get_order_with_id(self, id):
        return self.active_orderAs[id]

    def market_to_file(self, bist_time):
        """
        Called by process_execute_order() each time an orderE is matched with the market
        Open the file in append mode, create if it does not exist
        """
        line_list = [
            bist_time,
            self.OpenAsks.min_price,
            self.OpenBids.max_price,
            self.OpenBids.volume + self.OpenAsks.volume
        ]
        line = ",".join([str(x) for x in line_list])
        with open(self.price_file, 'a') as f:
            f.write(line + "\n")

    def match_orders(self, orderE, side, id, qty_to_match, price, best_price_list):
        """
        Called by process_execute_order() whenever the price of the order is worse or equal to the market price
        and thus needs to be processed as if it was a market order 
        This will be called inside a while loop until qty_to_match is 0 or best_price_list is empty

        Args:
            side: "B" or "S", the side incoming order (and not the side of the best price list)
            id: the id of the incoming order
            qty_to_match: the qty of the incoming order that has not been matched yet
            best_price_list: OrderList of orders at the best price on the other side of the book 
        Returns:
            qty_to_match: the orderE qty that is not matched yet
            matched_trades: a list of trades that have been matched
        """
        # match the orders as long as there is quantity to trade and the order list is not empty
        while ((qty_to_match > 0) and (len(best_price_list) != 0)):

            # where we start checking the queue of orders at the same price
            head_order = best_price_list.head_order

            # If the head_order can match the entire qty_to_match, updates the head_order quantity before setting the qty_to_match to 0
            if qty_to_match < head_order.qty:
                qty_matched = qty_to_match
                remaining_head_qty = head_order.qty - qty_to_match
                head_order.update_qty_not_matched(remaining_head_qty)
                qty_to_match = 0

            # If the head_order qty is equal to the qty_to_match, removes the head order from the correct orderTree depending on the side
            # before setting the qty_to_match to 0
            elif qty_to_match == head_order.qty:
                qty_matched = qty_to_match
                head_order.update_qty_not_matched(0)
                if side == 'B':
                    self.OpenAsks.remove_order_by_id(head_order.id)
                else:
                    self.OpenBids.remove_order_by_id(head_order.id)
                qty_to_match = 0

            # If the qty_to_match is greater than the head_order qty, 
            # the process is just like the one above, except, at the end qty_to_match is set to the remaining quantity after consuming the head order
            else:
                qty_matched = head_order.qty
                head_order.update_qty_not_matched(0)
                if side == 'B':
                    self.OpenAsks.remove_order_by_id(head_order.id)
                else:
                    self.OpenBids.remove_order_by_id(head_order.id)
                qty_to_match -= qty_matched

            # Construct the transaction record
            transaction_dict = {
                # 'timestamp': orderE.bist_time,
                'price': price,
                'qty': qty_matched,
                }

            if side == 'B':
                transaction_dict['party1'] = [head_order.id, 'bid']
                transaction_dict['party2'] = [id, 'ask']
            else:
                transaction_dict['party1'] = [head_order.id, 'ask']
                transaction_dict['party2'] = [id, 'bid']
            self.trades.append(transaction_dict)

        return qty_to_match

    def process_delete_order(self, orderD):
        """
        Called from process_order() when an orderD arrives
        """
        id = orderD.id
        orderA = self.get_order_with_id(id)
        orderA.add_to_order_stack(orderD)
        self.remove_order_from_book(orderA)
        
    def process_execute_order(self, orderE):
        """
        Called by process_order() when msg_type == "E"
        """
        qty_not_matched  = orderE.qty    # this will be decremented if processing as if a market order, otherwise, inserted into book as it is
        orderA           = self.get_order_with_id(orderE.id)
        side             = orderA.side
        id               = orderE.id
        price            = orderA.price

        # orderE now has fully populated attributes from orderA
        orderA.process_execute_order(orderE)
        # if orderA.qty_not_executed == 0, then the order is fully executed and needs to be removed from the book
        if orderA.qty_not_executed == 0:
            self.remove_order_from_book(orderA)

        # # =================== TEST CODE ===================
        # if side == "B":
        #     self.OpenBids.insert_order(orderE)
        #     self.bids_test_dict[id] = orderE
        # else:
        #     self.OpenAsks.insert_order(orderE)
        #     self.asks_test_dict[id] = orderE
        # # =================== TEST CODE ===================

        # If orderE price is worse than the market price, then calls match_orders as if it was a market order
        # If it is better than the market price, then it adds the order to the book
        # Make sure that qty is greater than 0, self.OpenAsks is not empty
        if side == "B":
            while ((qty_not_matched > 0) and (self.OpenAsks) and (price >= self.OpenAsks.min_price)) == True:
                best_price_list = self.OpenAsks.min_list()

                qty_not_matched = self.match_orders(side, orderE, id, qty_not_matched, price, best_price_list)
                orderE.update_qty_not_matched(qty_not_matched)
            # When done with matching the order, append the market info to self.time_series 
            self.market_to_file(orderE.bist_time)

            # If there is remaning qty, then add it to the book
            if qty_not_matched > 0:
                orderE.qty = qty_not_matched
                self.OpenBids.insert_order(orderE)
                # todo - remove after tests
                self.bids_test_dict[id] = orderE
        # In this case the side is "S"
        else:
            while ((qty_not_matched > 0) and self.OpenBids and (price <= self.OpenBids.max_price)) == True:
                best_price_list = self.OpenBids.max_list()

                qty_not_matched = self.match_orders(side, orderE, id, qty_not_matched, price, best_price_list)
                orderE.update_qty_not_matched(qty_not_matched)
            # When done with matching the order, append the market info to self.time_series 
            self.market_to_file(orderE.bist_time)

            # If there is remaning qty, then add it to the book
            if qty_not_matched > 0:
                orderE.qty = qty_not_matched
                self.OpenAsks.insert_order(orderE)
                # todo - remove after tests
                self.asks_test_dict[id] = orderE

    def remove_order_from_book(self, orderA):
        """
        Called from:
        1- process_delete_order() when an orderD arrives
        2- process_execute_order() when an orderE that turns consumed flag of orderA to True
        """
        id = orderA.id

        # first remove from active_orderAs
        del self.active_orderAs[id]
        # add to the list of closed orders
        self.closed_orderAs.append(orderA)

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
        side     = quote_dict["side"]

        try:
            # check if msg_type == valid
            assert msg_type in ['A', 'E', 'D'], "msg_type must be either A, E or D"
            assert side in ['B', 'S'], "side must be either B or S"

            # make sure that network_time, bist_time, id are positive integers
            assert quote_dict["network_time"] != "0", "network_time must be a positive integer"
            assert quote_dict["bist_time"]    != "0", "bist_time must be a positive integer"
            assert quote_dict["id"]           != "0", "id must be a positive integer"

            # =============== ATTRIBUTES FROM ARGS ============== 
            quote_dict["network_time"] = int(quote_dict["network_time"])
            quote_dict["bist_time"]    = int(quote_dict["bist_time"])
            quote_dict["qty"]          = int(quote_dict["qty"])
            quote_dict["price"]        = float(quote_dict["price"])
            quote_dict["que_loc"]      = int(quote_dict["que_loc"])
        except AssertionError as e:
            raise ValueError(e)

        order = None
        if msg_type == "A":
            order = orderA(**quote_dict)
            self.active_orderAs[order.id] = order  # adding the order to the active_orderAs
        elif msg_type == "E":
            order = orderE(quote_dict)
            self.process_execute_order(order)
        elif msg_type == "D":
            order = orderD(quote_dict)
            self.process_delete_order(order)

        if self.debug_mode:
            print("Order:\n", order)
            if msg_type in ["A", "D"]:
                self.display_open_and_closed_orders()
            else:
                self.display_book()

    def get_volume_at_price(self, price):
        """
        Returns the volume at a price
        """
        volume = None
        if price in self.OpenBids:
            volume = self.OpenBids.price_dict[price].volume
        if price in self.OpenAsks:
            volume = self.OpenAsks.price_dict[price].volume

        return volume

    def display_open_and_closed_orders(self):
        """
        Prints the number of open and closed orders
        """
        print("OPEN ORDERS:")
        print(len(self.active_orderAs))
        [print(order) for order in self.active_orderAs.values()]
        print("CLOSED ORDERS:")
        print(len(self.closed_orderAs))
        [print(order) for order in self.closed_orderAs]

    def tape_dump(self, fname, fmode, tmode):
        """
        Dumps the list of trades to a file

        PARAMETERS:
        fname - file name
        fmode - file mode
        tmode - tape mode - if "wipe" then the file is wiped after writing
        """
        dump_file = open(fname, fmode)
        for tape_item in self.trades:
            # dump_file.write('%s, %s, %s\n' % (tape_item['time'], tape_item['price'], tape_item['qty']))
            dump_file.write(f"{tape_item['time']}, {tape_item['price']}, {tape_item['qty']}\n")
        dump_file.close()
        if tmode == 'wipe':
                self.trades = []

    def display_book(self):
        # # length of active_orderAs
        # print(f"\nACTIVE ORDERS: {len(self.active_orderAs)} items")
        # pprint(self.active_orderAs)
        # # print("\nASKS:")
        # # pprint(self.asks_test_dict)
        # # print("\nBIDS:")
        # # pprint(self.bids_test_dict)
        # print(f"\nCLOSED ORDERS: {len(self.closed_orderAs)} items")
        # pprint(self.closed_orderAs)
        print()
        print(self)

    def __str__(self):
        fileStr = StringIO()

        fileStr.write("======================== Bids ========================\n")
        if self.OpenBids != None and len(self.OpenBids) > 0:
            # prints RBTree items of OrderTree objects, which are OrderList objects, which then call OrderList object's __str__ method
            # this way we print orders awaiting execution at each price level
            for k, v in self.OpenBids.price_tree.items(reverse=True):
                fileStr.write('%s' % v)

        fileStr.write("\n========================= Asks =========================\n")
        if self.OpenAsks != None and len(self.OpenAsks) > 0:
            for k, v in self.OpenAsks.price_tree.items():
                fileStr.write('%s' % v)

        fileStr.write("\n======================== Trades ========================\n")
        if self.trades != None and len(self.trades) > 0:
            num = 0
            for entry in self.trades:
                if num < 5:
                    # trade_str = f"{entry['qty']} @ {entry['price']} ({entry['bist_time']})\n"
                    # fileStr.write(trade_str)
                    fileStr.write(pformat(entry, width=1, compact=True))
                    fileStr.write("\n")
                    num += 1
                else:
                    break
        fileStr.write("\n")
        return fileStr.getvalue()