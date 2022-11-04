# from six.moves import cStringIO as StringIO
from io import StringIO
import heapq

class OrderQue(object):
    """
    This is a priority queue, implemented as a min heap list
    which stores orderE objects, sorted by their que_loc attribute.

    Used by OrderTree to store the list of orders at a given price level. 

    At each operation, the head element (self.heap at index 0)
    remains the one with the lowest que_loc value 
    """

    def __init__(self):
        self.volume = 0  # Total order volume
        self.heap   = [] 
        self.length = len(self.heap)

    def get_head(self):
        """
        Returns the orderE object at the head of the heap,
        which is the orderE with the lowest que_loc
        """
        return self.heap[0]

    def append_order(self, order):
        """
        order: orderE object
        """
        self.length += 1
        self.volume += order.qty_not_matched
        heapq.heappush(self.heap, order)

    def remove_head_order(self):
        """
        Removes the orderE object at the head of the heap,
        which is the orderE with the lowest que_loc
        """
        self.volume -= self.heap[0].qty_not_matched
        self.length -= 1
        if len(self) == 0:
            return
        heapq.heappop(self.heap)

    def remove_order_by_key(self, key):
        """
        Removes the orderE object with the given key from the heap
        """
        # from self.head delete the orderE object with the given key
        for i, order in enumerate(self.heap):
            if order.key == key:
                self.volume -= order.qty_not_matched
                self.length -= 1
                del self.heap[i]
                heapq.heapify(self.heap)
                break

    def __len__(self):
        return self.length

    def __str__(self):
        """
        Returns a the list of orders as a chain of their of qty_not_matched values, 
        after printing the size and total volume
        """
        file_str = StringIO()
        # we add up the order qty_not_matched of all orders before displaying them, 
        # since self.vol doesn't account for difference in volume of orders that has been only partially matched
        qty_list = [order.qty_not_matched for order in self.heap]
        # file_str.write("tot: {}, vol: {} ,{}| ".format(self.length, sum(qty_list)))
        file_str.write(f"| tot: {self.length:>4} | vol: {sum(qty_list):>7} |")

        # UNCOMMENT IF WANT TO DISPLAY THE LIST AS A CHAIN OF ORDER qty_not_matched OR que_loc VALUES
        # for order in self.heap:
        #     # displays heap as a chain of qty_not_matched values 
        #     # file_str.write(f"-> {order.qty_not_matched}")

        #     # displays heap as a chain of que_loc values 
        #     file_str.write(f"-> {order.que_loc}")
        return file_str.getvalue()
