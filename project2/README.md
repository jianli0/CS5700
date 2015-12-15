###Members:
- Kexi Long 001729512
- Jian Li 001731714

###Library Denpendencies:
- beautifulsoup4

###High-level Design:
Our Crawler communicates with the server in a asynchrnous fashion. We utilize the `select()` system call to poll a bunch of sockets that are readable or writable, then process then.
To achive this asynchrouness, we implement `Worker` class to record the current IO state and other metadata on this TCP connection.
And a `Crawler` class to execute the Event Loop to poll and process IO events.
An instance of `Crawler` possesses a lot of workers and each worker holds an persistent connection to the server. In every iteration of the Event Loop, IO-ready workers read/write parts of data from/to the socket until all the data is processed. Finally, `Worker` call the callback function given by `Crawler` to process read-in data.

###Challenges:
The major challenge is to implement the Event Loop, and determine what kind of information `Worker` should record. We went through a lot of documents, the most useful one is `Understanding Event-driven I/O Pattern` from Python Cookbook 3th Edition.

###Test:
We test each method in each class separately on `fring.ccs.neu.edu`. In terms of the Event Loop, we added some printout calls in between some key procedures to see if the data being processed is what we are expecting.

