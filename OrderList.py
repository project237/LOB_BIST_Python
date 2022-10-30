# from collections import deque

# TODO - try reimplementing this using a deque

# from six.moves import cStringIO as StringIO
from io import StringIO

class OrderList(object):
    # class OrderList:
    # TODO - retry with the commented out code above
    # TODO - raplace all Order references with orderA references
    # TODO - Implement order priority comparison (involves que_loc, bist_time, network_time)

    """ 
    List of order that await execution at the same price
    The price is the key of the dictionary inside the price_dict attribute of the OpenOrders object

    Credit for the class - https://github.com/abcabhishek/PyLimitOrderBook/blob/120bb03f9989bb1e471d59e0b4ede6203c05ec96/pylimitbook/orderList.py
    """ 
    def __init__(self):
        self.head_order = None
        self.tail_order = None
        self.length     = 0
        self.volume     = 0  # Total order volume
        self.last       = None

    def __len__(self):
        return self.length

    def __iter__(self):
        self.last = self.head_order
        return self

    def next(self):
        if self.last == None:
            raise StopIteration
        else:
            return_val = self.last
            self.last = self.last.next_order
            return return_val

    __next__ = next # Python 3.x compatibility

    def append_order(self, order):
        """
        order: orderE object
        """
        if len(self) == 0:
            order.next_order           = None
            order.prev_order           = None
            self.head_order            = order
            self.tail_order            = order
        else:
            order.prev_order           = self.tail_order
            order.next_order           = None
            self.tail_order.next_order = order
            self.tail_order            = order
        self.length += 1
        self.volume += order.qty

    def remove_order(self, order):
        self.volume -= order.qty
        self.length -= 1
        if len(self) == 0:
            return
        # Remove from list of orders
        next_order = order.next_order
        prev_order = order.prev_order
        if next_order != None and prev_order != None:
            next_order.prev_order = prev_order
            prev_order.next_order = next_order
        elif next_order != None:
            next_order.prev_order = None
            self.head_order = next_order
        elif prev_order != None:
            prev_order.next_order = None
            self.tail_order = prev_order

    def __str__(self):
        file_str = StringIO()
        for order in self:
            file_str.write(f"{order}\n")
            # file_str.write("%s\n" % str(order))
        return file_str.getvalue()