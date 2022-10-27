from bintrees import FastRBTree

class OpenOrders:
    """
    Both bids and asks have their own OpenOrders object which sorts them in their order of priority to be matched,
    first by the price, then by the que_loc of the order. 
    The main data structure used for sorting the orders is a Reb Black Tree. We also use two dicts,
    One that stores order_list objects by price, and one that stores orders by order_id.
    """
    def __init__(self):
        tree = FastRBTree()
        order_dict = {}      # key: order_id, value: Order
        price_dict = {}      # key: price, value: OrderList

        # these get updated every time an price is inserted or removed
        min_price = None     
        max_price = None

    def __len__(self):
        return len(self.order_dict)

    def get_min_price(self):
        return self.min_price

    def get_max_price(self):
        return self.max_price

    def __repr__(self):
        pass

    def __str__(self):
        pass

    # ============================= ORDER METHODS =============================

    def insert_order(self, order):
        pass

    def remove_order(self, order):
        pass

    def get_order_by_id(self, order_id):
        return self.order_dict[order_id]

    def update_order(self, order):
        pass

    # ============================= PRICE METHODS =============================

    def insert_price(self, price):
        pass

    def remove_price(self, price):
        pass

    def get_order_list_at_price(self, price):
        return self.price_dict[price]