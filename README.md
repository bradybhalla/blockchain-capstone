# blockchain-capstone

For a CS capstone project in my senior year of high school, I made my own blockchain from scratch and used it to maintain a cryptocurrency.  Some highlights of this project were:

 - Implementing the Proof of Work consensus algorithm
 - Learning about digital signatures and hash functions and implementing ECDSA
 - Creating a small network of miners which communicated using HTTP and allowed the cryptocurrency to function

For more information, read [my final paper](Capstone_Final_Paper.pdf).  

Here is a simple description of each file, and further comments are contained within the code:

 - [blockchain.py](blockchain.py): Validates blocks and organizes them into the actual blockchain.  Uses Proof of Work to resolve conflicts between branches of the blockchain.
 - [client.py](client.py): Creates a crypto wallet which can be used to store account information and interact with miners to transact on the blockchain.
 - [elliptic.py](elliptic.py): Math for elliptic curves.  Used for digital signatures.
 - [mine.py](mine.py): Running this file creates a miner and maintains a blockchain with any other nodes it connects to.
 - [miner.py](miner.py): Subclass of a node which mines cryptocurrency and distributes newly mined blocks.
 - [node.py](node.py): Node classes which run servers and communicate with other nodes to make sure everyone has the same blockchain recorded. Uses locks to make sure it is thread safe.
 - [signature.py](signature.py): Implementation of multiple signature algorithms.
 - [transaction.py](transaction.py): Transaction and Ledger classes which record and verify transactions on the blockchain.
 - [utils.py](utils.py): Utility functions for prime numbers, hashing, and verification.
