        
class order:
    """
    Creates an order objet as a result of parsing single row of order csv file. 
    """
    def __init__(self, network_time, bist_time, msg_type, asset_name, side, price, que_loc, qty, id):

        # =================== INPUT CHECKS ===================  

        try:
            # check if msg_type is valid
            assert msg_type in ['A', 'E', 'D']

            # make sure that network_time, bist_time, id are positive integers
            assert network_time != "0"
            assert bist_time    != "0"
            assert id           != "0"
        except AssertionError:
            raise ValueError
        
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

    def __hash__(self):
        return hash(self.id)
