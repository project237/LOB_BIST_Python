# LOB_BIST_Python
Limit Order Book implementation and backtest engine written in Python. 

## Instructions
1. Make sure the data file is in the same directory as the main file, and its name assigned to the INPUT_FILE_NAME variable at the top of the main.py
2. Run main.py, this will run the order data through an OrderEngine instance, which at the end will save the output files into /output directory, after creating if it doesn't exist. 
   1. To display the numerical data, run an instance of view_LOB_output.ipynb as it is. 
   2. View LOB.txt to see the user output, which prints an image of the orderbook each time trades are processed, along with other info. 
   3. Don't forget to save (or just rename) these files before running main.py again, since it will overwrite the files. 
   
## Program Overview
### Order Types and Interactions
  1. **A (add)** orders sit on a list maintained by `OrderEngine` order book class waiting to be bought or sold at a given price but cannot enter market trades or get into the order queue at any given price unless an E order with the same id arrives the book. 
     - As observed in the order data, it has one-to-many mapping to E orders and one-to-one mapping to D orders. 
     - Thus we maintain them as a map (python dict) with O(1) lookup time with id as their key.  
  2. **E (execute)** orders all have an id associated with one A order that came before. Upon arrival, they "activate" the portion of the A orders that their qty value specifies (If it is not the case that they have equal qty values, in which case only one E order will arrive for the A order.)  
     - At this point, if price of the A order is better than the current market price, the E order is added to the order queue (class `OrderQue`) of the price, which is sorted acc. to the `que_loc` of E orders in it. This is the queue where every such E order is awaiting execution with the one having the smallest `que_loc` being at the head of the queue, and thus, the next in line to be matched by incoming market orders. 
     - If the order A price is worse or equal to the current market price (of the opposite side), then the E order is executed as if a market order and matches other E orders waiting in the queue of the best price queue until it runs out of its original `qty` value. Thus the volume of this trade will equal to that value. 
     - If during this process, the queue of the best price runs out of orders, the queue is removed from the `OrderTree` structure of the opposing side (which maintain price queues) and the incoming market order(s) start matching the queue of the next best price.
     - Upon arrival the E order is added to the `order_stack` (a python list of dicts) of the A order before updating the `orderA.qty_not_executed` attribute. If this is now zero, orderA has no incoming secondary orders left and is removed from `OrderEngine.active_orderAs` dict and is added to `OrderEngine.closed_orderAs` (a list). 
     - As observed in the order data, A orders have one-to-many relationship to E orders. 
  3. **D (delete)** orders simply cancel the active orderA that is maintained by `OrderEngine.active_orderAs` , by looking up its id and deleting from the dictionary. After this, the D order is added to the `order_stack` of the A order before it is inserted to the `OrderEngine.closed_orderAs` list.
     - As observed in the order data, A orders have one-to-one mapping to D orders (only 1 needed to cancel). 
     - If it is the case that the A orders canceled by the D order have Execute orders with the same id awaiting execution on the order book, these E orders are 
     then removed from the `OrderTree` as well as `OrderQue` objects that contain them.

### Data Structures Used
- Price Queue's (class `OrderQue`) are maintained as a min-heap since each time an order on the best price list is fully matched, we are insterested in only getting the next element with the smallest `que_loc` value. Min heap was the perfect choice since it has O(1) lookup time for the min element and O(logN) for both insertion and pop (removal of the smallest element).
- The `OrderEngine` class has two "price trees" that maintain the `OrderQue`'s sorted acc to their prices at all times. One is for bid prices and one for asks. Each of these priority queues (with prices as their keys) is maintained as a Red-Black-Tree data structure which keeps the prices sorted at each operation of removing a price (after all orders matched) or inserting a new one (for orderEs that are better than the market price, but don't have their price on the OrderTree yet). Both of these operations are O(logN) worst case time complexity. 
