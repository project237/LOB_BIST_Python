# from six.moves import cStringIO as StringIO
from io import StringIO
import heapq

class OrderQue(object):
    # |* = heapified|
    # class OrderList:
    # todo - overload comparison operators on orderE by comparing que_loc
    # todo - implement getting the head order (without popping it) from the heap

    def __init__(self):
        # |*|
        self.volume = 0  # Total order volume
        self.heap   = [] 
        self.length = len(self.heap)

        # heapq.heapify(self.queue)
        # self.head_order = None
        # self.tail_order = None
        # self.last       = None

    def __len__(self):
        # |*|
        return self.length

    def append_order(self, order):
        # |*|
        """
        order: orderE object
        """
        self.length += 1
        self.volume += order.qty_not_matched
        heapq.heappush(self.heap, order)

    def remove_order(self, order):
        # |*|
        self.volume -= order.qty_not_matched
        self.length -= 1
        if len(self) == 0:
            return
        heapq.heappop(self.heap)

    def __str__(self):
        # |*|
        file_str = StringIO()
        qty_list = [order.qty_not_matched for order in self.heap]
        file_str.write("tot: {}, vol: {} | ".format(self.length, sum(qty_list)))
        for order in qty_list:
            file_str.write(f"-> {order}")
        return file_str.getvalue()