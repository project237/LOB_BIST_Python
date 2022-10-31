#!/usr/bin/python

from bintrees import FastRBTree
from OrderList import OrderList

class OrderTree(object):
# class OrderTree:
# TODO -try commented above
    """
    Both bids and asks have their own Tree object which sorts them in their order of priority to be matched,
    first by the price, then by the que_loc of the order. 
    The main data structure used for sorting the orders is a Reb Black Tree. We also use two dicts,
    One that stores order_list objects by price, and one that stores orders by order_id.

    Credit - https://github.com/abcabhishek/PyLimitOrderBook/blob/master/pylimitbook/tree.py
    """
    def __init__(self):
        self.price_tree = FastRBTree() # Key: price, Value: OrderList object
        self.volume = 0
        self.price_dict = {}  # Key: price, Value: OrderList object
        self.order_dict = {}  # Key: orderE.key, Value: orderE object
        self.min_price = None
        self.max_price = None
    
    def __str__(self):
        # print keys and values of price_dict on seperate lines
        out_str = ""
        for key, value in self.price_dict.items():
            out_str += f"{key}: {value}\n"
        return out_str

    def __contains__(self, key):
        return key in self.price_dict

    def __len__(self):
        return len(self.order_dict)

    def get_price(self, price):
        return self.price_dict[price]

    def get_order(self, key):
        return self.order_dict[key]

    def create_price(self, price):
        new_list = OrderList()
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

    def insert_order(self, order):
        """
        order: orderE object
        Will be called by send_order_to_book() method of OrderEngine class, when a new orderE is received
        """
        if order.price not in self.price_dict:
            self.create_price(order.price)

        # order = Order(tick, self.price_dict[tick.price])
        order.add_order_list(self.price_dict[order.price])

        self.price_dict[order.price].append_order(order)
        self.order_dict[order.key] = order
        self.volume += order.qty

    def remove_order_by_id(self, key):
        """
        Called by OrderEngine.match_orders() whenever an incoming orderE is matched on orderE on the OrderTree
        
        Returns:
            removed: Bool, True if the price_list has been removed from the tree 
        """
        removed = False
        order = self.order_dict[key]
        self.volume -= order.qty
        order.order_list.remove_order(order)
        if len(order.order_list) == 0:
            self.remove_price(order.price)
            removed = True
        del self.order_dict[key]
        return removed

    def get_price_list(self, price):
        """
        Called by OrderEngine.match_orders() to get the OrderList object of the incoming orderE price
        """
        return self.price_dict[price]
        
    # def max_list(self):
    #     return self.price_dict[self.max_price]

    # def min_list(self):
    #     return self.price_dict[self.min_price]
