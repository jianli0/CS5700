########################
## HighLevel Approach ##
########################

Our solution is to divide the problem into three layers (Application/TCP/IP) as in the ISO model. There are not strictly three layers in our project, but we follows the idea solving problem layer by layer.

The application layer takes input of user, makes the request and calls sending process, as shown in figure below.A connection was built following three way handshake before the sending process. After packed by TCP and IP layer, the final IP_datagram is generated, and the final IP_datagram is sent to the corresponding remote_host.

We keep monitoring all the packets received, if the source of it is the corresponding remote_host, we unpack the IP_Datagram layer by layer, as shown in figure below. 
advertised window;


Send:
=========
|Payload|
=========

pack_tcp_segment -> TCP_Segment

========================
|TCP_Header| + |Payload|
========================

pack_ip_datagram ->IP_Datagram

======================================
|IP_Header| + |TCP_Header| + |Payload|
======================================

Recv:

IP_Datagram
===================================
|IP_Header| + |TCP_Header| + |Data|
===================================

unpack_ip_datagram -> TCP_Segment

=====================
|TCP_Header| + |Data|
=====================

unpack_tcp_segment -> Data

======
|Data|
======


###################################
## TCP / IP features Implemented ##
###################################

We implemented all features mentioned in the instructions.

IP features implemented(all required features implemented):

1) validate the checksums of incoming packets.

2) set the correct version, header length and total length, protocol identifier and checksum in each outgoing packet.

3) correctly set the source and destination IP in each outgoing packet.

TCP features implemented: 

1) verify the checksums of incoming TCP packets, and generate correct checksums for outgoing packets

2) select a valid local port to send traffic on

3) perform the three-way handshake

4) handle connection teardown 

5) handle sequence and acknowledgement numbers 

6) manage the advertised window as fit

7) timeout functionality 

8) receive out-of-order incoming packets and put them back into the correct order 

9) identify and discard duplicate packets

10) implement a basic congestion window

######################
## Challenges Faced ##
######################

1) used socket.IPPROTO_RAW (in python) to receive packets: we didn’t pay much attention to the instructions and only use one socket for sending and receiving packets in our program, however receive operation gives a error message. We build another socket.IPPROTO_TCP for receive packets as instructed to solve this problem.

2) extra operations in three way handshake: in our first implementation of three way handshake, we implement a  fourth operation which receives the packet from the server after the third ack packet. We capture this received packet and found the sequence number doesn’t match. After two hour struggling we figured out the receive operation is unnecessary.   


 