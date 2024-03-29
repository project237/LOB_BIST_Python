from io             import StringIO
from LOB.OrderTypes import orderA, orderE, orderD
from LOB.OrderTree  import OrderTree
import os
import concurrent.futures
import time

class InvalidOrder(Exception):
    """
    Raised when an incoming order line fails to match criteria set by OrderEngine.process_order()
    """
    pass

class OrderEngine(object):
    """
    Saves the market as well as the trade data to a new directory called "output" (creates it if it doesn't exist)
    Default file names are "market_data.csv" and "trades.csv"
    
    ASSUMPTIONS:
    1- Column order_id, together with bist_time uniquely identifies the orderE, thus there cannot be orderEs with the same order_id and bist_time 
    """
    def __init__(self, debug_mode=False, concurrent_mode=False, price_file="market_data.csv", trades_file="trades.csv", order_book_file="LOB.txt", orderA_file="closed_orders.txt", lob_file="LOB.csv"):
        self.debug_mode          = debug_mode # if True, prints the order book, closed_orderAs and active_orderAs after processing each order
        self.concurrent_mode       = concurrent_mode # if True, all parallelized versions of the functions will be used inside run_with_file()
        self.price_file          = price_file # file name where the market info will be recorded
        self.trades_file         = trades_file # file name where the trades will be recorded
        self.order_book_file     = order_book_file # file name where the order book (as well as other output) will be recorded
        self.price_file_stream   = StringIO() # stream where the market info will be recorded
        self.trades_file_stream  = StringIO() # stream where the trades will be recorded
        self.output_stream       = StringIO() # stream where the output will be recorded
        self.lob_stream          = StringIO() # stream where the order book will be recorded
        self.OpenBids            = OrderTree(isbid=True)
        self.OpenAsks            = OrderTree(isbid=False)
        self.trades              = [] # A list of trades that have been matched
        self.closed_orderAs      = [] # List of orderA's that have been fully matched or canlceled, which esentially contains other orders
        self.active_orderAs      = {} # A dict of orderA objects that are not yet fully matched, key = order id, value = order object
        self.time_series         = [] # A list of dicts, each dict contains the order book at a specific time
        self.last_trades         = [] # A list of last trades that have been matched
        self.last_line           = None # Counter for the last line index that was processed
        self.tot_lines           = None # Total number of lines in the file
        self.orderA_file         = orderA_file # file name where the orderA's will be recorded
        self.lob_file            = lob_file # file name where the order book will be recorded

        # add columns to the price file
        self.price_file_stream.write("bist_time,ask,bid,volume\n")
        self.trades_file_stream.write("bist_time,price,qty,bid_key,ask_key,\n")
        self.lob_stream.write("bist_time,ask_price1,ask_vol1,ask_price2,ask_vol2,ask_price3,ask_vol3,bid_price1,bid_vol1,bid_price2,bid_vol2,bid_price3,bid_vol3\n") 

    def run_with_file(self, file_name):
        """
        This is the top level function that is called to run the OrderEngine on the entire input order file
        """
        # start the timer, use perf_counter() for high resolution timer
        start = time.perf_counter()

        num_lines = 0
        with open(file_name, "r") as f:
            num_lines = sum(1 for line in f)
        self.tot_lines = num_lines


        with open(file_name, "r") as f:
            for i, l in enumerate(f):
                self.last_line = i
                
                # terminate if we reach the end of the file
                if l in ["", "\n"] or (i == num_lines-1): 
                    self.output_stream.write("\n================================= END OF FILE REACHED =================================")
                    print("\n================================= END OF FILE REACHED =================================")
                    print("\n================================ SAVED FILES TO /output ===============================")
                    print()
                    break

                try:
                    self.process_order(l)
                except InvalidOrder as e:
                    # This error doesn't raise any exception, so we ignore the invalid order and process the next one
                    self.output_stream.write(f'\nInvalid order at line {(i+1)} due to \n==> {e}')
                except Exception as e :
                    self.output_stream.write(f'\nError: "{e}" at line {(i+1)}')
                    self.output_stream.write("\nPrinting Order Book and exiting...")
                    self.output_stream.write(str(self))
                    raise e
            self.output_stream.write(self.display_final())

        # record start of the save_to_file for timing
        start_save = time.perf_counter() 
        if self.concurrent_mode:
            self.save_to_file_concurrent()
        else:
            self.save_to_file()
        # stop the timer
        end = time.perf_counter()

        print("\n============================== DISPLAYING CONFIGURATIONS ==============================")
        print("DEBUG_MODE    :", self.debug_mode)
        print("CONCURRENT_MODE :", self.concurrent_mode)
        print("INPUT_FILE    :", file_name)
        # print the time it took to run the OrderEngine
        print(f"\n========================= PROGRAM COMPLETED IN: {end-start    :0.4f} SECONDS =======================")
        print(f"\n========================= SAVING COMPLETED IN: {end-start_save:0.4f} SECONDS =========================")

    def process_order(self, line):
        """
        Top level method that processes the incoming order
        Processes a line from the input file, turns into order and calls the right method depending on the msg_type
        """
        quote_list = line.strip("\n").split(",")

        keys_list  = ["network_time", "bist_time", "msg_type", "asset_name", "side", "price", "que_loc", "qty", "id"]
        quote_dict = dict(zip(keys_list, quote_list))
        msg_type = quote_dict["msg_type"]
        side     = quote_dict["side"]
        self.last_trades = []

        try:
            assert len(quote_list) == 9        , "quote_list must have 9 elements"
            assert msg_type in ['A', 'E', 'D'] , "msg_type must be either A, E or D"
            assert side in ['B', 'S']          , "side must be either B or S"

            # make sure that network_time, bist_time, id are positive integers
            assert quote_dict["network_time"] != "0", "network_time must be a positive integer"
            assert quote_dict["bist_time"]    != "0", "bist_time must be a positive integer"
            assert quote_dict["id"]           != "0", "id must be a positive integer"

            # =============== ATTRIBUTES FROM ARGS ============== 
            quote_dict["network_time"] = int(quote_dict["network_time"])
            quote_dict["bist_time"]    = int(quote_dict["bist_time"])
            quote_dict["qty"]          = int(quote_dict["qty"])
            quote_dict["price"]        = float(quote_dict["price"])
            quote_dict["que_loc"]      = int(quote_dict["que_loc"])
        except Exception as e:
            raise InvalidOrder(e)

        order = None
        if msg_type == "A":
            order = orderA(**quote_dict, ord_engine=self)
            self.active_orderAs[order.id] = order  # adding the order to the active_orderAs
        elif msg_type == "E":
            order = orderE(quote_dict)
            try:
                self.process_execute_order(order)
            except Exception as e:
                raise e                
        elif msg_type == "D":
            order = orderD(quote_dict)
            try:
                self.process_delete_order(order)
            except Exception as e:
                raise e

        # print the book (or open and closed orderA's) if debug_mode is True
        if self.debug_mode:
            if msg_type in ["A", "D"]:
                self.display_open_and_closed_orders()
                return
            else:
                self.output_stream.write("Incoming Order:\n\n", order)
                print(self)
                return

    def process_delete_order(self, orderD):
        """
        Called by process_order() when msg_type == "D"
        """
        id = orderD.id
        try:
            orderA = self.get_order_with_id(id)
        except Exception:
            raise InvalidOrder("ADD order with id {} does not exist in the book".format(id))
        orderA.process_delete_order(orderD)
        # orderA.add_to_order_stack(orderD) already called from within orderA
        self.remove_order_from_book(orderA)

    def process_execute_order(self, orderE):
        """
        Called by process_order() when msg_type == "E"
        """
        qty_not_matched  = orderE.qty_not_matched # this will be decremented if processing as if a market order, otherwise, inserted into book as it is
        try:
            orderA = self.get_order_with_id(orderE.id)
        except Exception:
            raise InvalidOrder("ADD order with id {} does not exist in the book".format(orderE.id))
        orderA           = self.get_order_with_id(orderE.id)
        side             = orderA.side

        # orderE now has fully populated attributes from orderA
        orderA.process_execute_order(orderE) 

        # list of trades for output
        trades      = []
        last_trades = []

        # If orderE price is worse than the market price, then calls match_orders as if it was a market order
        # If it is better than the market price, then it adds the order to the book
        # Make sure that qty is greater than 0, self.OpenAsks is not empty
        if side == "B":
            if self.OpenAsks.volume > 0:
                qty_not_matched, last_trades = self.OpenAsks.process_order(orderE)
                trades.extend(last_trades)

            # If there is remaning qty, then add it to the book
            if qty_not_matched > 0:
                self.OpenBids.insert_order(orderE)

        # In this case the side is "S"
        else:
            if self.OpenBids.volume > 0:
                qty_not_matched, last_trades = self.OpenBids.process_order(orderE)
                trades.extend(last_trades)

            # If there is remaning qty, then add it to the book
            if qty_not_matched > 0:
                self.OpenAsks.insert_order(orderE)

        self.last_trades = last_trades

        # If any trades have been made, append the market and trades info to their output streams 
        if self.last_trades != []:
            self.market_to_file(orderE.bist_time)
            self.trades_to_file(trades)
            self.lob_stream.write(str(orderE.bist_time) + ",")
            self.output_stream.write(str(self))
            self.output_stream.write("New orderE matched:\n\n" + str(orderE))

    def remove_order_from_book(self, orderA):
        """
        Called from:
        1- process_delete_order() when an orderD arrives
        2- process_execute_order() when an orderE that turns consumed flag of orderA to True
        """
        id = orderA.id

        # first remove from active_orderAs
        del self.active_orderAs[id]
        # add to the list of closed orders
        self.closed_orderAs.append(orderA)

    def get_order_with_id(self, id):
        """
        Arguments:
            id: str, id of the orderA
        Returns:
            orderA: orderA object
        """
        return self.active_orderAs[id]

    def get_volume_at_price(self, price):
        """
        Returns volume at a price
        """
        volume = None
        if price in self.OpenBids:
            volume = self.OpenBids.price_dict[price].volume
        if price in self.OpenAsks:
            volume = self.OpenAsks.price_dict[price].volume
        return volume

    def trades_to_file(self, trades):
        """
        Called by process_execute_order() 
        Adds the trades to the output stream, that will be saved to file when save_to_file() is called

        Arguments:
            trades: list of trade dicts
        """
        for trade in trades:
            if trade is not []:
                line = ",".join([str(x) for x in trade])
                self.trades_file_stream.write(line + "\n")
    
    def market_to_file(self, bist_time):
        """
        Called by process_execute_order() each time an orderE is matched with the market
        Adds the market data to the output stream, that will be saved to file when save_to_file() is called

        Arguments:
            bist_time: int, time of the orderE
        """
        line_list = [
            bist_time,
            self.OpenAsks.min_price,
            self.OpenBids.max_price,
            self.OpenBids.volume + self.OpenAsks.volume
        ]
        line = ",".join([str(x) for x in line_list])
        # with open(self.price_file, 'a') as f:
        #     f.write(line + "\n")
        self.price_file_stream.write(line + "\n")
    
    def save_to_file(self):
        """
        Saves the both self.price_file_stream self.trades_file_stream into files with names self.price_file and self.trades_file
        """
        # open directory "ouput" if it does not exist
        if not os.path.exists("output"):
            os.makedirs("output")
        # open self.price_file under "output" directory, and write the contents of self.price_file_stream into it
        with open(os.path.join("output", self.price_file), 'w') as f:
            f.write(self.price_file_stream.getvalue())
        # same for self.trades_file
        with open(os.path.join("output", self.trades_file), 'w') as f:
            f.write(self.trades_file_stream.getvalue())
        with open(os.path.join("output", self.order_book_file), 'w') as f:
            f.write(self.output_stream.getvalue())
        with open(os.path.join("output",self.lob_file), 'w') as f:
            f.write(self.lob_stream.getvalue())
        with open(os.path.join("output",self.orderA_file), 'w') as f:
            [f.write(str(x) + "\n") for x in self.closed_orderAs]
            # json.dump([str(x) for x in self.closed_orderAs], f)

    def write_price_file(self):
        """
        Writes the price filestream into the price file
        """
        # open self.price_file under "output" directory, and write the contents of self.price_file_stream into it
        with open(os.path.join("output", self.price_file), 'w') as f:
            f.write(self.price_file_stream.getvalue())

    def write_trades_file(self):
        """
        Writes the trades filestream into the trades file
        """
        # same for self.trades_file
        with open(os.path.join("output", self.trades_file), 'w') as f:
            f.write(self.trades_file_stream.getvalue())
    
    def write_order_book_file(self):
        """
        Writes the order book filestream into the order book file
        """
        with open(os.path.join("output", self.order_book_file), 'w') as f:
            f.write(self.output_stream.getvalue())

    def write_lob_file(self):
        """
        Writes the lob filestream into the lob file
        """
        with open(os.path.join("output", self.lob_file), 'w') as f:
            f.write(self.lob_stream.getvalue())

    def write_orderA_file(self):
        """
        Writes the orderA filestream into the orderA file
        """
        with open(os.path.join("output", self.orderA_file), 'w') as f:
            [f.write(str(x) + "\n") for x in self.closed_orderAs]
            # json.dump([str(x) for x in self.closed_orderAs], f)

    def save_to_file_concurrent(self):
        """
        Parallel version of save_to_file(), uses concurrent.futures.ProcessPoolExecutor to write to files in parallel
        """
        # open directory "ouput" if it does not exist
        if not os.path.exists("output"):
            os.makedirs("output")
        
        # create a list of futures
        futures = []
        # create a ProcessPoolExecutor
        # with concurrent.futures.ProcessPoolExecutor() as executor:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # submit the methods that save the filestreams to the executor, one by one
            futures.append(executor.submit(self.write_price_file, self.price_file_stream, self.price_file))
            futures.append(executor.submit(self.write_trades_file, self.trades_file_stream, self.trades_file))
            futures.append(executor.submit(self.write_order_book_file, self.output_stream, self.order_book_file))
            futures.append(executor.submit(self.write_orderA_file, self.closed_orderAs, self.orderA_file))
            futures.append(executor.submit(self.write_lob_file, self.lob_stream, self.lob_file))
            # wait for all futures to complete
            concurrent.futures.wait(futures)
    
    def display_open_and_closed_orders(self):
        """
        Prints the number of open and closed orders
        """
        print("\nNumber of A orders:")
        print(f"Open: {len(self.active_orderAs)}")
        print(f"Closed: {len(self.closed_orderAs)}")

        # UCOMMENT TO SEE THE LIST OF CLOSED ORDERS
        # [print(order) for order in self.active_orderAs.values()]
        # print("CLOSED ORDERS:")
        # print(len(self.closed_orderAs))
        # [print(order) for order in self.closed_orderAs]

    def display_final(self):
        """
        A user friendly method that prints string representation of the book. 
        """
        S = "\nTotal trades recorded: " + str(len(self.closed_orderAs))
        return S

    def __str__(self):
        S = ""
        last_line = self.last_line
        percent = round(last_line / self.tot_lines * 100, 2)
        S += f"\n=================================================== At Line {last_line+1:>7} ({percent:>5}%) =========="
        print(f"\n=============================== At Line {last_line+1:>7} ({percent:>5}%) ==============================")

        S += "\n================= Asks =================\n"
        if self.OpenAsks != None and len(self.OpenAsks) > 0:
            # S += (str(self.OpenAsks))
            ask_str, ask_list = self.OpenAsks.top_order_book()
            S += ask_str
            askline = ",".join([str(x) for x in ask_list])
            self.lob_stream.write(str(askline) + ",")


        S += "\n================= Bids =================\n"
        if self.OpenBids != None and len(self.OpenBids) > 0:
            # S += (str(self.OpenBids))
            bid_str, bid_list = self.OpenBids.top_order_book()
            S += bid_str
            bidline = ",".join([str(x) for x in bid_list])
            self.lob_stream.write(str(bidline) + "\n")

        S += "\n================ Trades ================\n"
        if self.last_trades != []:
            for entry in self.last_trades:
                trade_str = f"| p: {entry[1]:>5} | qty: {entry[2]:>5}                |\n"
                S += trade_str
                # S += (pformat(entry, width=1, compact=True))
        else:
            S += "| No trades were made.                 |\n"
        S += "\n"
        return S
