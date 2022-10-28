
from pprint import pformat

class ActiveOrder:
    """
    Internal order type. 
    The class of orders that will sit on the book (if not processed immediately) as a result of calling an
    Execute order to an Active order.
    """
    def __init__(self, qty, orderA):
        self.qty      = qty
        self.orderA   = orderA
        self.side     = orderA.side
        self.price    = orderA.price
        self.que_loc  = orderA.que_loc

    def __repr__(self):
        return pformat(vars(self), indent=4, width=1)

class orderA:
    """
    User order type.
    The primary order type that has the entire quote fields. 
    """
    def __init__(self, network_time, bist_time, msg_type, asset_name, side, price, que_loc, qty, id):
        # Attributes from qoute
        self.network_time     = network_time
        self.bist_time        = bist_time
        self.msg_type         = msg_type
        self.asset_name       = asset_name
        self.side             = side
        self.price            = price
        self.que_loc          = que_loc
        self.qty              = qty
        self.id               = id

        # Other attributes
        self.qty_not_executed = qty
        self.consumed         = False

    def __repr__(self):
        return pformat(vars(self), indent=4, width=1)

class orderE:
    """
    User order type.
    Secondary order type that only has the fields necessary to execute an order.
    """
    def __init__(self, dict):
        self.msg_type     = dict["msg_type"]
        self.id           = dict["id"]
        self.network_time = dict["network_time"]
        self.bist_time    = dict["bist_time"]
        self.qty          = dict["qty"]

    def __repr__(self):
        return pformat(vars(self), indent=4, width=1)


class orderD:
    """
    User order type.
    Secondary order type that only has the fields necessary to delete an order.
    """
    def __init__(self, dict):
        self.msg_type     = dict["msg_type"]
        self.id           = dict["id"]
        self.network_time = dict["network_time"]
        self.bist_time    = dict["bist_time"]

    def __repr__(self):
        return pformat(vars(self), indent=4, width=1)


class Order:
    """
    Creates an order objet as a result of parsing single row of order csv file. 
    """
    def __init__(self, network_time, bist_time, msg_type, asset_name, side, price, que_loc, qty, id):

        # =================== INPUT CHECKS ===================  

        # We raise ValueError instead of generic AssertionError to be able to handle with no ambiguity
        try:
            # check if msg_type is valid
            assert msg_type in ['A', 'E', 'D']

            # make sure that network_time, bist_time, id are positive integers
            assert network_time != "0"
            assert bist_time    != "0"
            assert id           != "0"

            # =============== ATTRIBUTES FROM ARGS ============== 
            self.network_time = int(network_time)
            self.bist_time    = int(bist_time)
            self.msg_type     = msg_type
            self.asset_name   = asset_name
            self.side         = side
            self.qty          = int(qty)
            self.price        = float(price)
            self.que_loc      = int(que_loc)
            self.id           = id
        except AssertionError:
            raise ValueError
        
        # =============== INFERRED ATTRIBUTES ===============  

        # will be set to False if order is cancelled
        self.active = None
        if self.msg_type in ['A', 'E']:
            self.active = True

    

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    def cancel(self):
        self.active = False

    # todo - Add the function that decides the order precedence 
    # def __eq__(self, other):
    #     return self.__dict__ == other.__dict__

    # def __ne__(self, other):
    #     return not self.__eq__(other)

    # def __lt__(self, other):
    #     return self.timestamp < other.timestamp

    # def __le__(self, other):
    #     return self.timestamp <= other.timestamp

    # def __gt__(self, other):
    #     return self.timestamp > other.timestamp

    # def __ge__(self, other):
    #     return self.timestamp >= other.timestamp

