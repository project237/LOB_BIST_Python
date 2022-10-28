#!/usr/bin/python

from bintrees import FastRBTree

from OrderTypes import ActiveOrder
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
        self.price_tree = FastRBTree()
        self.volume = 0
        self.price_dict = {}  # Map from price -> order_list object
        self.order_dict = {}  # Order ID to Order object
        self.min_price = None
        self.max_price = None

    def __len__(self):
        return len(self.order_dict)

    def get_price(self, price):
        return self.price_dict[price]

    def get_order(self, id_num):
        return self.order_dict[id_num]

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

    def order_exists(self, id_num):
        return id_num in self.order_dict

    def insert_tick(self, tick):
        if tick.price not in self.price_dict:
            self.create_price(tick.price)
        order = Order(tick, self.price_dict[tick.price])
        # TODO - Initialize to ActiveOrder object correctly

        self.price_dict[order.price].append_order(order)
        self.order_dict[order.id_num] = order
        self.volume += order.qty

    def update_order(self, tick):
        order = self.order_dict[tick.id_num]
        original_volume = order.qty
        if tick.price != order.price:
            # Price changed
            order_list = self.price_dict[order.price]
            order_list.remove_order(order)
            if len(order_list) == 0:
                self.remove_price(order.price)
            self.insert_tick(tick)
            self.volume -= original_volume
        else:
            # Quantity changed
            order.update_qty(tick.qty, tick.price)
            self.volume += order.qty - original_volume

    def remove_order_by_id(self, id_num):
        order = self.order_dict[id_num]
        self.volume -= order.qty
        order.order_list.remove_order(order)
        if len(order.order_list) == 0:
            self.remove_price(order.price)
        del self.order_dict[id_num]

    def max(self):
        return self.max_price

    def min(self):
        return self.min_price