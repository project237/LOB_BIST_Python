from order import order

class OrderEngine:
    def __init__(self):
        self.all_orders    = [] # might remove that
        self.active_orders = {}

    def process_order(self, ord):

        # =================== INPUT CHECKS ===================
        # make sure order is an instance of order class
        assert isinstance(ord, order)

        self.all_orders.append(ord)
        
        # add order to active_orders if it is active
        if ord.active:
            self.active_orders[ord.id] = ord

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)