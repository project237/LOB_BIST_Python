
# from collections import deque

# TODO - try reimplementing this using a deque

class OrderList(object):
    # class OrderList:
    # TODO - retry with the commented out code above
    """ 
    List of order that await execution at the same price
    The price is the key of the dictionary inside the price_dict attribute of the OpenOrders object

    Credit for the class - https://github.com/DrAshBooth/PyLOB/blob/master/src/PyLOB/orderlist.py
    """ 

    def __init__(self):
        self.headOrder = None
        self.tailOrder = None
        self.length = 0
        self.volume = 0    # Total share volume
        self.last = None
        
    def __len__(self):
        return self.length
    
    def __iter__(self):
        self.last = self.headOrder
        return self
    
    def __next__(self):
        if self.last == None:
            raise StopIteration
        else:
            returnVal = self.last
            self.last = self.last.nextOrder
            return returnVal
        
    def getHeadOrder(self):
        return self.headOrder
    
    def appendOrder(self, order):
        if len(self) == 0:
            order.nextOrder = None
            order.prevOrder = None
            self.headOrder = order
            self.tailOrder = order
        else:
            order.prevOrder = self.tailOrder
            order.nextOrder = None
            self.tailOrder.nextOrder = order
            self.tailOrder = order
        self.length += 1
        self.volume += order.qty
        
    def removeOrder(self, order):
        self.volume -= order.qty
        self.length -= 1
        if len(self) == 0:
            return
        # Remove from list of orders
        nextOrder = order.nextOrder
        prevOrder = order.prevOrder
        if nextOrder != None and prevOrder != None:
            nextOrder.prevOrder = prevOrder
            prevOrder.nextOrder = nextOrder
        elif nextOrder != None:
            nextOrder.prevOrder = None
            self.headOrder = nextOrder
        elif prevOrder != None:
            prevOrder.nextOrder = None
            self.tailOrder = prevOrder
            
    def moveTail(self, order):
        if order.prevOrder != None:
            order.prevOrder.nextOrder = order.nextOrder
        else:
            # Update the head order
            self.headOrder = order.nextOrder
        order.nextOrder.prevOrder = order.prevOrder
        # Set the previous tail order's next order to this order
        self.tailOrder.nextOrder = order
        order.prevOrder = self.tailOrder
        self.tailOrder = order
        order.nextOrder = None
        
    def __str__(self):
        from io import StringIO
        file_str = StringIO()
        for order in self:
            file_str.write("%s\n" % str(order))
        return file_str.getvalue()