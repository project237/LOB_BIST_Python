
from io import StringIO
from OrderTypes import orderA, orderE, orderD
from OrderTree import OrderTree
from pprint import pprint, pformat

class InvalidOrder(Exception):
    """
    Raised when an incoming order line fails to match criteria set by OrderEngine.process_order()
    """
    pass

class OrderEngine:
    """
    ASSUMPTIONS:
    1- An order A cannot receive an orderE and orderD at different times
    2- Column order_id, together with bist_time uniquely identifies the orderE, thus there cannot be orderEs with the same order_id and bist_time 
    """
    def __init__(self, debug_mode=False, price_file=None):
        self.debug_mode          = debug_mode # if True, prints the order book, closed_orderAs and active_orderAs after processing each order
        self.price_file          = price_file # file name where the market info will be recorded
        self.OpenBids            = OrderTree()
        self.OpenAsks            = OrderTree()
        self.trades              = [] # A list of trades that have been matched
        self.closed_orderAs      = [] # List of orderA's that have been fully matched or canlceled, which esentially contains other orders
        self.active_orderAs      = {} # A dict of orderA objects that are not yet fully matched, key = order id, value = order object
        self.time_series         = [] # A list of dicts, each dict contains the order book at a specific time
        self.last_trades         = [] # A list of last trades that have been matched

        # add columns to the price file if a file name is provided
        if self.price_file is not None:
            with open(self.price_file, 'w') as f:
                f.write("bist_time,ask,bid,volume\n")

    def process_order(self, line):
        """
        Top level method that processes the incoming order
        Processes a line from the input file, turns into order and calls the right method depending on the msg_type
        """
        quote_list = line.strip("\n").split(",")

        keys_list  = ["network_time", "bist_time", "msg_type", "asset_name", "side", "price", "que_loc", "qty", "id"]
        quote_dict = dict(zip(keys_list, quote_list))
        msg_type = quote_dict["msg_type"]
        side     = quote_dict["side"]

        try:
            assert len(quote_list) == 9, "quote_list must have 9 elements"
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
            raise InvalidOrder(e)

        order = None
        if msg_type == "A":
            order = orderA(**quote_dict)
            self.active_orderAs[order.id] = order  # adding the order to the active_orderAs
        elif msg_type == "E":
            order = orderE(quote_dict)
            self.last_trades = []
            self.process_execute_order(order)
        elif msg_type == "D":
            order = orderD(quote_dict)
            self.process_delete_order(order)

        # print the book (or open and closed orderA's) if debug_mode is True
        if self.debug_mode:
            if msg_type in ["A", "D"]:
                self.display_open_and_closed_orders()
                return
            else:
                print("Incoming Order:\n", order)
                self.display_book()
                return

    def process_delete_order(self, orderD):
        """
        Called by process_order() when msg_type == "D"
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
        key              = orderE.key
        price            = orderA.price

        # orderE now has fully populated attributes from orderA
        orderA.process_execute_order(orderE)
        # if orderA.qty_not_executed == 0, then the order is fully executed and needs to be removed from the book
        if orderA.qty_not_executed == 0:
            self.remove_order_from_book(orderA)

        # If orderE price is worse than the market price, then calls match_orders as if it was a market order
        # If it is better than the market price, then it adds the order to the book
        # Make sure that qty is greater than 0, self.OpenAsks is not empty
        if side == "B":
            best_price = self.OpenAsks.min_price
            while ((qty_not_matched > 0) and (self.OpenAsks) and (price >= best_price)) == True:
                price_list = self.OpenAsks.get_price_list(best_price)

                qty_not_matched, price_removed = self.match_orders(side, key, qty_not_matched, best_price, price_list)
                orderE.update_qty_not_matched(qty_not_matched)
                best_price = self.OpenAsks.min_price

            # If there is remaning qty, then add it to the book
            if qty_not_matched > 0:
                self.OpenBids.insert_order(orderE)

        # In this case the side is "S"
        else:
            best_price = self.OpenBids.max_price
            while ((qty_not_matched > 0) and self.OpenBids and (price <= self.OpenBids.max_price)) == True:
                price_list = self.OpenBids.get_price_list(best_price)

                qty_not_matched, price_removed = self.match_orders(side, key, qty_not_matched, best_price, price_list)
                orderE.update_qty_not_matched(qty_not_matched)
                best_price = self.OpenBids.max_price

            # If there is remaning qty, then add it to the book
            if qty_not_matched > 0:
                self.OpenAsks.insert_order(orderE)

        # When done with matching the order, append the market info to self.time_series 
        self.market_to_file(orderE.bist_time)

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

    def match_orders(self, side, key, qty_to_match, price, price_list):
        """
        Called by process_execute_order() whenever the price of the order is worse or equal to the market price
        and thus needs to be processed as if it was a market order 
        This will be called inside a while loop until qty_to_match is 0 or price_list is empty

        Args:
            side         - "B" or "S", the side incoming order (and not the side of the best price list)
            key          - the key of the incoming order
            qty_to_match - the qty of the incoming order that has not been matched yet
            price_list   - OrderList of orders at the best price on the other side of the book 
        Returns:
            qty_to_match  - the orderE qty that is not matched yet
            price_removed - A flag that indicates if the price_list removed from the book
        """
        price_removed = False 

        # match the orders as long as there is quantity to trade and the order list is not empty
        while ((qty_to_match > 0) and (len(price_list) != 0)):

            # where we start checking the queue of orders at the same price
            head_order = price_list.head_order

            # If the head_order can match the entire qty_to_match, updates the head_order quantity before setting the qty_to_match to 0
            if qty_to_match < head_order.qty_not_matched:
                qty_matched = qty_to_match
                remaining_head_qty = head_order.qty_not_matched - qty_to_match
                head_order.update_qty_not_matched(remaining_head_qty)
                qty_to_match = 0

            # If the head_order qty is equal to the qty_to_match, removes the head order from the correct orderTree depending on the side
            # before setting the qty_to_match to 0
            elif qty_to_match == head_order.qty_not_matched:
                qty_matched = qty_to_match
                head_order.update_qty_not_matched(0)
                if side == 'B':
                    price_removed = self.OpenAsks.remove_order_by_id(head_order.key)
                else:
                    price_removed = self.OpenBids.remove_order_by_id(head_order.key)
                qty_to_match = 0

            # If the qty_to_match is greater than the head_order qty, 
            # the process is just like the one above, except, at the end qty_to_match is set to the remaining quantity after consuming the head order
            else:
                qty_matched = head_order.qty_not_matched
                head_order.update_qty_not_matched(0)
                if side == 'B':
                    price_removed = self.OpenAsks.remove_order_by_id(head_order.key)
                else:
                    price_removed = self.OpenBids.remove_order_by_id(head_order.key)
                qty_to_match -= qty_matched

            # Construct the transaction record
            transaction_dict = {
                # 'timestamp': orderE.bist_time,
                'price': price,
                'qty': qty_matched,
                }

            if side == 'B':
                transaction_dict['bid'] = [head_order.key]
                transaction_dict['ask'] = [key]
            else:
                transaction_dict['bid'] = [key]
                transaction_dict['ask'] = [head_order.key]
            self.trades.append(transaction_dict)
            self.last_trades.append(transaction_dict)

        return qty_to_match, price_removed

    def get_volume_at_price(self, price):
        """
        Returns volume at a price
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
        print("\nNumber of A orders:")
        print(f"Open: {len(self.active_orderAs)}")
        print(f"Closed: {len(self.closed_orderAs)}")
        # [print(order) for order in self.active_orderAs.values()]
        # print("CLOSED ORDERS:")
        # print(len(self.closed_orderAs))
        # [print(order) for order in self.closed_orderAs]

    def tape_dump(self, fname, fmode, tmode):
        """
        Todo: test this
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
        """
        A user friendly method that prints string representation of the book. 
        """
        print(self)

    def __str__(self):
        fileStr = StringIO()

        fileStr.write("\n========================= Bids =========================\n")
        if self.OpenBids != None and len(self.OpenBids) > 0:
            fileStr.write(str(self.OpenBids))

        fileStr.write("\n========================= Asks =========================\n")
        if self.OpenAsks != None and len(self.OpenAsks) > 0:
            fileStr.write(str(self.OpenAsks))

        fileStr.write("\n======================== Trades ========================\n")
        if self.last_trades != None and len(self.last_trades) > 0:
            for entry in self.last_trades:
                trade_str = f"P: {entry['price']} Q: {entry['qty']}\n"
                fileStr.write(trade_str)
                # fileStr.write(pformat(entry, width=1, compact=True))
        else:
            fileStr.write("No trades were made.")
        fileStr.write("\n")
        return fileStr.getvalue()