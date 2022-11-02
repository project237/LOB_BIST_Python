
from pprint import pformat

class orderA:
    """
    The primary order type that has the entire quote fields. 
    """
    def __init__(self, network_time, bist_time, msg_type, asset_name, side, price, que_loc, qty, id):
        self.network_time     = network_time
        self.bist_time        = bist_time
        self.msg_type         = msg_type
        self.asset_name       = asset_name
        self.side             = side
        self.price            = price
        self.que_loc          = que_loc
        self.id               = id
        self.qty              = qty
        self.qty_not_executed = qty
        self.canceled         = False   # Turns True if an orderD is received
        self.order_stack      = []      # List of processed seconary orders (E and D) associated with this orderA

    def process_execute_order(self, orderE: "orderE"):
        """
        Called by process_order() when msg_type == "E"
        Each time after calling this method, we check if qty_not_executed == 0 and in that case we remove the orderA from the active_orderAs in OrderEngine 
        """
        qty = orderE.qty
        if self.qty >= qty:
            # will turn to 0 if they are equal
            self.qty_not_executed -= qty
        else:
            raise ValueError("orderE.qty is greater than orderA.qty")

        self.add_to_order_stack(orderE)
        orderE.populate_attributes_from_orderA(self)

    def add_to_order_stack(self, order):
        """
        Adds the secondary (D or E) order to the order_stack of the orderA 
        whenever orderA is either deleted or fully matched.
        """
        self.order_stack.append(order)
        if order.msg_type == "D":
            self.canceled = True

    def __str__(self):
        str_dict = {
            "msg_type": self.msg_type,
            "side": self.side,
            "price": self.price,
            "id": self.id,
            "qty": self.qty,
            "qty_not_executed": self.qty_not_executed,
            "canceled": self.canceled,
            "que_loc": self.que_loc,         
            "network_time": self.network_time, 
            "bist_time": self.bist_time,
        }
        return pformat(str_dict, indent=4, width=1, compact=True)

class orderE:
    """
    Secondary order type that only has the fields necessary to execute an order.
    
    The class of orders that will sit on the book (if not processed immediately) as a result of calling 
    process_execute_order() on an orderA object.
        
    self.key is the attribute which orderE's will be indexed by in OrderTree.order_dict, 
    this is the only combination of two columns that is unique for orderE's
    """
    def __init__(self, dict):
        self.id                = dict["id"]
        self.qty               = dict["qty"]
        self.qty_not_matched   = dict["qty"]
        self.msg_type          = dict["msg_type"]
        self.network_time      = dict["network_time"]
        self.bist_time         = dict["bist_time"]
        self.key               = dict["id"] + str(dict["bist_time"]) 
        self.side              = None
        self.price             = None
        self.que_loc           = None
        self.order_list        = None
        self.next_order        = None
        self.prev_order        = None

    def populate_attributes_from_orderA(self, orderA: orderA):
        """
        Populates the attributes of orderE with the attributes of orderA.
        """
        self.side         = orderA.side
        self.price        = orderA.price
        self.que_loc      = orderA.que_loc

    def update_qty_not_matched(self, qty):
        """
        Called by OrderList when an order is fully or partially matched.
        """
        self.qty_not_matched = qty

    def add_order_list(self, order_list):
        """
        Will be called by insert_order() of OrderTree class when an order is inserted into the tree
        """
        self.order_list = order_list

    def __str__(self):
        str_dict = {
            "msg_type": self.msg_type,
            "side": self.side,
            "price": self.price,
            "id": self.id,
            "qty": self.qty,
            "qty_not_matched": self.qty_not_matched,
            "que_loc": self.que_loc
            # "network_time": self.network_time, 
            # "bist_time": self.bist_time,
            # "que_loc": self.que_loc            
        }
        return pformat(str_dict, indent=4, width=1, compact=True)

    def __eq__(self, other):
        # compares self.que_loc
        return self.que_loc == other.que_loc

    def __ge__(self, other):
        # compares self.que_loc
        return self.que_loc >= other.que_loc
    
    def __gt__(self, other):
        # compares self.que_loc
        return self.que_loc > other.que_loc
    
    def __le__(self, other):
        # compares self.que_loc
        return self.que_loc <= other.que_loc

    def __lt__(self, other):
        # compares self.que_loc
        return self.que_loc < other.que_loc
    
    def __ne__(self, other):
        # compares self.que_loc
        return self.que_loc != other.que_loc

class orderD:
    """
    Secondary order type that only has the fields necessary to delete an orderA.
    """
    def __init__(self, dict):
        self.msg_type     = dict["msg_type"]
        self.id           = dict["id"]
        self.network_time = dict["network_time"]
        self.bist_time    = dict["bist_time"]

    def __str__(self):
        return pformat(vars(self), indent=4, width=1, compact=True)