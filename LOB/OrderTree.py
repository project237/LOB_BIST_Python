#!/usr/bin/python

from LOB.OrderQue   import OrderQue
from LOB.OrderTypes import orderE
from bintrees       import FastRBTree

class OrderTree(object):
    """
    Both bids and asks have their own Tree object which sorts them in their order of priority to be matched,
    first by the price, then by the que_loc of the order. 
    The main data structure used for sorting the orders is a Reb Black Tree. We also use two dicts,
    One that stores order_list objects by price, and one that stores orders by order_id.
    """
    def __init__(self, isbid: bool):
        self.isbid      = isbid # True if bid, False if ask
        self.price_tree = FastRBTree() # Key: price, Value: OrderQue object
        self.volume     = 0
        self.price_dict = {}  # Key: price, Value: OrderQue object
        self.order_dict = {}  # Key: orderE.key, Value: orderE object
        self.min_price  = None
        self.max_price  = None
    
    def __str__(self):
        # print keys and values of price_dict on seperate lines
        out_str = ""
        # reverse = False if self.isbid else True
        for key, value in sorted(self.price_dict.items(), reverse=True):
            qty_list = [order.qty_not_matched for order in value.heap]
            # file_str.write("tot: {}, vol: {} ,{}| ".format(self.length, sum(qty_list)))
            out_str += (f"| p: {key:>5}: | tot: {value.length:>4} | vol: {sum(qty_list):>7} |\n")
            # out_str += f"| p: {key:>5}: {value}\n"
        
        out_str += f"|                                      |\n"
        out_str += f"| Volume       : {self.volume:>9}             |\n"
        out_str += f"| Total Orders : {len(self.order_dict):>9}             |\n"
        return out_str

    def __contains__(self, key):
        return key in self.price_dict

    def __len__(self):
        return len(self.order_dict)

    def get_price(self, price):
        return self.price_dict[price]

    def get_order(self, key):
        return self.order_dict[key]
    
    def get_order_que(self, price):
        """
        Called by OrderEngine.match_orders() to get the OrderQue object of the incoming orderE price
        """
        return self.price_dict[price]

    def create_price(self, price):
        new_list = OrderQue()
        self.price_tree.insert(price, new_list)
        self.price_dict[price] = new_list
        if self.max_price == None or price > self.max_price:
            self.max_price = price
        if self.min_price == None or price < self.min_price:
            self.min_price = price

    def remove_price(self, price):
        self.price_tree.remove(price)
        del self.price_dict[price]

        # update min and max price
        if self.max_price == price:
            try:
                self.max_price = max(self.price_tree)
            except ValueError:
                self.max_price = None
        if self.min_price == price:
            try:
                self.min_price = min(self.price_tree)
            except ValueError:
                self.min_price = None

    def price_exists(self, price):
        return price in self.price_dict

    def order_exists(self, key):
        return key in self.order_dict

    def match_orders_at_price(self, orderE, qty_to_match, order_que, price):
        """
        Called by OrderTree.match_order_loop() whenever an incoming orderE is at or worse than the market price

        Arguments:
            orderE: orderE object
            qty_to_match: int, qty of incoming orderE that has not been matched yet
            order_que: OrderQue object, at the same price as incoming orderE
        Returns:
            qty_not_matched: int, the qty of the incoming orderE that has not been matched
            trades: list of Trade lists, will be later saved to file at OrderEngine.save_to_file()
        """

        trades = []

        # match the orders as long as there is quantity to trade and the order list is not empty
        while ((qty_to_match > 0) and (len(order_que) != 0)):

            # where we start checking the queue of orders at the same price
            head_order = order_que.get_head()

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
                self.remove_order_by_key(head_order.key)
                head_order.update_qty_not_matched(0)
                qty_to_match = 0

            # If the qty_to_match is greater than the head_order qty, 
            # the process is just like the one above, except, at the end qty_to_match is set to the remaining quantity after consuming the head order
            else:
                qty_matched = head_order.qty_not_matched
                self.remove_order_by_key(head_order.key)
                head_order.update_qty_not_matched(0)
                qty_to_match -= qty_matched
            
            # Construct the transaction record
            bid_id, ask_id = None, None
            if orderE.side == 'B':
                bid_id = int(head_order.key)
                ask_id = int(orderE.key)
            else:
                bid_id = int(orderE.key)
                ask_id = int(head_order.key)

            transaction_list = [
                orderE.bist_time,
                price,
                qty_matched,
                bid_id,
                ask_id
            ]
            trades.append(transaction_list)

        return qty_to_match, trades

    def process_order(self, orderE):
        """
        Called by OrderEngine.process_execute_order() whenever an incoming orderE is at or worse than the market price

        Arguments:
            orderE: orderE object
        Returns:
            qty_not_matched: int, the qty of the incoming orderE that has not been matched
            trades: list of Trade dicts
        """
        qty_not_matched = orderE.qty_not_matched
        price           = orderE.price
        best_price      = self.max_price if self.isbid else self.min_price
        
        trades = []
        while ((qty_not_matched > 0) and (price <= best_price if self.isbid else price >= best_price)) == True:
            order_que = self.get_order_que(best_price)

            qty_not_matched, trades_at_price = self.match_orders_at_price(orderE, qty_not_matched, order_que, best_price)
            orderE.update_qty_not_matched(qty_not_matched)
            trades.extend(trades_at_price)

            # update best price
            best_price = self.max_price if self.isbid else self.min_price
        return qty_not_matched, trades

    def insert_order(self, order):
        """
        Will be called by send_order_to_book() method of OrderEngine class, when a new orderE is received

        Arguments:
            order: orderE object
        """
        if order.price not in self.price_dict:
            self.create_price(order.price)

        order_que = self.price_dict[order.price] 
        order.add_order_list(order_que)
        order_que.append_order(order)
        self.order_dict[order.key] = order
        self.volume += order.qty_not_matched
        # set the order_tree attribute of the orderE object
        order.set_order_tree(self)

    def remove_order_by_key(self, key, not_head=False):
        """
        Called when
        a- orderA.process_delete_order() whenever an incoming orderE has fully matched order(s) in OrderTree,
            in this case, not_head=True
        b- OrderTree.match_orders_at_price() whenever an orderE is cancelled

        Arguments:
            key: int, key of the orderE to be removed
        """
        order = self.order_dict[key]
        self.volume -= order.qty_not_matched
        if not_head:
            order.order_list.remove_order_by_key(key)
        else:
            order.order_list.remove_head_order()
        if len(order.order_list) == 0:
            self.remove_price(order.price)
        del self.order_dict[key]
