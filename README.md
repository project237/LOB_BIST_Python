<!-- TOC start -->
- [LOB\_BIST\_Python](#lob_bist_python)
  - [Instructions](#instructions)
  - [Program Overview](#program-overview)
    - [Order Types and Interactions](#order-types-and-interactions)
    - [Input File](#input-file)
    - [Output Files](#output-files)
    - [Data Structures Used](#data-structures-used)
    - [Concurrency](#concurrency)
      - [When Saving the Output Files](#when-saving-the-output-files)
<!-- TOC end -->
<!-- TOC --><a name="lob_bist_python"></a>
# LOB_BIST_Python
Limit Order Book implementation for ITCH protocol format in Python. 

<!-- TOC --><a name="instructions"></a>
## Instructions
1. Make sure the data file is in the same directory as the main file, and its name assigned to the INPUT_FILE_NAME variable at the top of the main.py
2. Run main.py, this will run the order data through an OrderEngine instance, which at the end will save the output files into /output directory, after creating if it doesn't exist. 
   1. To display the numerical data, run an instance of view_LOB_output.ipynb as it is. 
   2. View LOB.txt to see the user output, which prints an image of the orderbook each time trades are processed, along with other info. 
   3. Don't forget to save (or just rename) these files before running main.py again, since it will overwrite the files. 
   
<!-- TOC --><a name="program-overview"></a>
## Program Overview
<!-- TOC --><a name="order-types-and-interactions"></a>
### Order Types and Interactions
  1. **A (add)** orders sit on a list maintained by `OrderEngine` order book class waiting to be bought or sold at a given price but cannot enter market trades or get into the order queue at any given price unless an E order with the same id arrives the book. 
     - As observed in the order data, it has one-to-many mapping to E orders and one-to-one mapping to D orders. 
     - Thus we maintain them as a map (python dict) with O(1) lookup time with id as their key.  
  1. **E (execute)** orders all have an id associated with one A order that came before. Upon arrival, they "activate" the portion of the A orders that their qty value specifies (If it is not the case that they have equal qty values, in which case only one E order will arrive for the A order.)  
     - At this point, if price of the A order is better than the current market price, the E order is added to the order queue (class `OrderQue`) of the price, which is sorted acc. to the `que_loc` of E orders in it. This is the queue where every such E order is awaiting execution with the one having the smallest `que_loc` being at the head of the queue, and thus, the next in line to be matched by incoming market orders. 
     - If the order A price is worse or equal to the current market price (of the opposite side), then the E order is executed as if a market order and matches other E orders waiting in the queue of the best price queue until it runs out of its original `qty` value. Thus the volume of this trade will equal to that value. 
     - If during this process, the queue of the best price runs out of orders, the queue is removed from the `OrderTree` structure of the opposing side (which maintain price queues) and the incoming market order(s) start matching the queue of the next best price.
     - Upon arrival the E order is added to the `order_stack` (a python list of dicts) of the A order before updating the `orderA.qty_not_executed` attribute. If this is now zero, orderA has no incoming secondary orders left and is removed from `OrderEngine.active_orderAs` dict and is added to `OrderEngine.closed_orderAs` (a list). 
     - As observed in the order data, A orders have one-to-many relationship to E orders. 
  2. **D (delete)** orders simply cancel the active orderA that is maintained by `OrderEngine.active_orderAs` , by looking up its id and deleting from the dictionary. After this, the D order is added to the `order_stack` of the A order before it is inserted to the `OrderEngine.closed_orderAs` list.
     - As observed in the order data, A orders have one-to-one mapping to D orders (only 1 needed to cancel). 
     - If it is the case that the A orders canceled by the D order have Execute orders with the same id awaiting execution on the order book, these E orders are 
     then removed from the `OrderTree` as well as `OrderQue` objects that contain them.

<!-- TOC --><a name="input-file"></a>
### Input File
The single input file is GARAN.E.mini.csv contains info for each order the exchange receives on each line. The columns are:
-  `network_time`: The time stamp of the order client server when it is received (Omitted when processing the orders)
-  `bist_time`: The time stamp of the exchange server when the order is received. This is the time that is processed by the algorithm. 
-  `msg_type`: The order type of incoming order  
-  `asset_name`: Symbol for the stock being traded, all values are same since the file contains the order info for "GARAN" stock only.    
-  `asset_name`: Symbol for the share being traded, all values are same since the file contains the order info for a single share type.    
-  `side`: "B" for buy side orders and "S" for sell side orders.     
-  `price`: Price of the order, for Add type orders only.     
-  `que_loc`: The priority index for the order, the less the number, the higher the priority when matching orders of the same price.      
-  `qty`: Total share quantity of the order, for Add and Execute type orders only.
-  `order_id`: Identifier for the order, is unique for all orders that exist on the order book at each point in time. On the file, there can be duplicates since data source is recycling the id's for new incoming orders, only in cases where there is no other order on the book with the same id. 

<!-- TOC --><a name="output-files"></a>
### Output Files
- LOB.mini.txt
  - This text file contains the comprehensive cross section of the entire order book whenever an incoming Execute order is matched with other orders that exist on the book, the info of the incoming order as a json, as well as the info of trades that have been made as a result of matching these orders. Here is how each such cross section looks like:
  - ![My picture](LOB_output_sample.png)
- LOB.mini.csv
  - A csv that displays top 3 bid and ask prices of the order order, as well as their quantities, indexed by the unix timestamp of the exchange time, recorded each time any orders are matched.   
- market_data.mini.csv
  - A csv that contains both bid and ask prices, as well as the total order book volume indexed by the unix timestamp of the exchange time recorded after each trade.
- trades.mini.csv
  - A csv that, for each trade between two orders, contains their order keys, as well as traded price and quantity, indexed by the unix timestamp of the exchange time.  
- closed_orders.mini.txt
  - A text file that displays JSON of orderE attributes at the time each such order is either deleted or matched. Saved mainly for debugging purposes.     

<!-- TOC --><a name="data-structures-used"></a>
### Data Structures Used
- Price Queue's (class `OrderQue`) are maintained as a min-heap since each time an order on the best price list is fully matched, we are interested in only getting the next element with the smallest `que_loc` value. Min heap was the perfect choice since it has O(1) lookup time for the min element and O(logN) for both insertion and pop (removal of the smallest element).
- The `OrderEngine` class has two "price trees" that maintain the `OrderQue`'s sorted acc to their prices at all times. One is for bid prices and one for asks. Each of these priority queues (with prices as their keys) is maintained as a Red-Black-Tree data structure which keeps the prices sorted at each operation of removing a price (after all orders matched) or inserting a new one (for orderEs that are better than the market price, but don't have their price on the OrderTree yet). Both of these operations are O(logN) worst case time complexity. 

<!-- TOC --><a name="concurrency"></a>
### Concurrency
<!-- TOC --><a name="when-saving-the-output-files"></a>
#### When Saving the Output Files
In main.py, we instantiate an `OrderEngine` object before executing the order engine logic with the main method, `run_with_file`. One of the keyword arguments of the constructor is `concurrent_mode`, if this is set to True, will run `OrderEngine.save_to_file_concurrent()` which, at the last steps of `run_with_file` launches a pool of separate threads that writes the output data streams into 5 different output files, all at the same time, instead of writing to those files one-by-one. 

After testing an input file with 10k orders in it, the version where `OrderEngine.save_to_file_concurrent()` is used, the program has resulted in an average of **99.33%** of reduction in execution time when compared to `OrderEngine.save_to_file()` which is version of the method where files are saved sequentially.

Here is the table of the execution times measured.

| Sample Number | Concurrent execution time (secs) | Sequential execution time (secs) |
| ------------- | -------------------------------- | -------------------------------- |
| 1             | 0.0085                           | 0.7532                           |
| 2             | 0.005                            | 0.8082                           |
| 3             | 0.0035                           | 0.8533                           |
| 4             | 0.0052                           | 0.7638                           |
| 5             | 0.0043                           | 0.7767                           |
| Mean:         | 0.0053                           | 0.79104                          |
| % Reduction:  | 99.32999595                      |