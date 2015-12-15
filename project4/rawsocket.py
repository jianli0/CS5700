# import argparse
import sys
import socket
import struct
import time
from random import randint
from collections import namedtuple
from util import get_local_ip_port, checksum


SYN = 0 + (1 << 1) + (0 << 2) + (0 <<3) + (0 << 4) + (0 << 5)
ACK = 0 + (0 << 1) + (0 << 2) + (0 <<3) + (1 << 4) + (0 << 5)
SYN_ACK = 0 + (1 << 1) + (0 << 2) + (0 <<3) + (1 << 4) + (0 << 5)
FIN = 1 + (0 << 1) + (0 << 2) + (0 <<3) + (0 << 4) + (0 << 5)
FIN_ACK = 1 + (0 << 1) + (0 << 2) + (0 <<3) + (1 << 4) + (0 << 5)
PSH_ACK = 0 + (0 << 1) + (0 << 2) + (1 <<3) + (1 << 4) + (0 << 5)
IP_HDR_FMT = '!BBHHHBBH4s4s'
TCP_HDR_FMT = '!HHLLBBHHH'
PSH_FMT = '!4s4sBBH'
IPDatagram = namedtuple('IPDatagram', 'ip_tlen ip_id ip_frag_off ip_saddr ip_daddr data ip_check')
TCPSeg = namedtuple('TCPSeg', 'tcp_source tcp_dest tcp_seq tcp_ack_seq tcp_check data tcp_flags tcp_adwind')


class MyTCPSocket(object):
    ssocket = None
    rsocket = None
    remote_host = ''
    remote_port = -1
    local_host = ''
    local_port = -1
    send_buf = ''
    recv_buf = ''
    tcp_seq_num = 0
    tcp_ack_num = 0
    ip_id = 0
    status = -1
    adwind = {}
    cwind = {}


    def __init__(self):
        self.ssocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        self.rsocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        self.local_host = get_local_ip_port()
        self.local_port = randint(1001, 65535)
        

    def pack_ip_datagram(self, payload):
        '''
        Generate IP datagram.
        `payload` is TCP segment
        '''
        ip_tos = 0
        ip_tot_len = 20 + len(payload)
        ip_id = self.ip_id  #Id of this packet
        ip_frag_off = 0
        ip_ttl = 255
        ip_proto = socket.IPPROTO_TCP
        ip_check = 0
        ip_saddr = socket.inet_aton (self.local_host)
        ip_daddr = socket.inet_aton (self.remote_host)

        ip_ihl_ver = (4 << 4) + 5
        ip_header = struct.pack(IP_HDR_FMT, ip_ihl_ver, ip_tos, ip_tot_len, ip_id, ip_frag_off, ip_ttl, ip_proto, ip_check, ip_saddr, ip_daddr)
        ip_check = checksum(ip_header)

        ip_header = struct.pack(IP_HDR_FMT, ip_ihl_ver, ip_tos, ip_tot_len, ip_id, ip_frag_off, ip_ttl, ip_proto, ip_check, ip_saddr, ip_daddr)
        # print struct.unpack(IP_HDR_FMT, ip_header)
        return ip_header + payload
 
    def pack_tcp_segment(self, payload='', flag=ACK):
        '''
        Generate TCP segment.
        '''
        # tcp header fields
        tcp_source = self.local_port   # source port
        tcp_dest = self.remote_port   # destination port
        tcp_seq = self.tcp_seq_num
        tcp_ack_seq = self.tcp_ack_num
        tcp_doff = 5    #4 bit field, size of tcp header, 5 * 4 = 20 bytes
        tcp_window = socket.htons (5840)    #   maximum allowed window size
        tcp_check = 0
        tcp_urg_ptr = 0
        tcp_offset_res = (tcp_doff << 4) + 0
        tcp_flags = flag
 
        tcp_header = struct.pack(TCP_HDR_FMT, tcp_source, tcp_dest, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags,  tcp_window, tcp_check, tcp_urg_ptr)
         
        # pseudo header fields
        source_address = socket.inet_aton(self.local_host)
        dest_address = socket.inet_aton(self.remote_host)
        placeholder = 0
        protocol = socket.IPPROTO_TCP
        tcp_length = len(tcp_header) + len(payload)

        psh = struct.pack(PSH_FMT, source_address , dest_address , placeholder , protocol , tcp_length);
        psh = psh + tcp_header + payload;
        
        tcp_check = checksum(psh)

        tcp_header = struct.pack(TCP_HDR_FMT[:-2], tcp_source, tcp_dest, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags,  tcp_window) + struct.pack('H' , tcp_check) + struct.pack('!H' , tcp_urg_ptr)

        return tcp_header + payload

    def send(self, data='', flags=ACK):
        self.send_buf = data
        tcp_segment = self.pack_tcp_segment(data, flag=flags)
        ip_datagram = self.pack_ip_datagram(tcp_segment)
        self.ssocket.sendto(ip_datagram, (self.remote_host, self.remote_port))

    def recv(self, size=65536, delay=180):
        self.rsocket.settimeout(delay)
        start = time.time()
        elapsed = 0
        try:
            while True:
                data = self.rsocket.recv(size)
                ip_datagram = self.unpack_ip_datagram(data)
                if ip_datagram.ip_daddr != self.local_host or ip_datagram.ip_check != 0 or ip_datagram.ip_saddr != self.remote_host:
                    continue
                # print ip_datagram
                tcp_seg = self.unpack_tcp_segment(ip_datagram.data)
                if tcp_seg.tcp_source != self.remote_port or tcp_seg.tcp_dest != self.local_port or tcp_seg.tcp_check != 0:
                    continue
                return tcp_seg

        except socket.timeout as e:
            raise e

        raise socket.timeout

    def connect(self, host, port):
        # Three-way handshake
        self.remote_host = host
        self.remote_port = port
        self.tcp_seq_num = randint(0, 65535)
        self.ip_id = randint(0, 65535)
        self.rsocket.settimeout(60)

        try:
            tcp_seg = self.recv()

            if tcp_seg.tcp_flags != SYN_ACK:
                print 'connect failed'
                return
            print tcp_seg
            self.tcp_seq_num = tcp_seg.tcp_ack_seq
            self.tcp_ack_num = tcp_seg.tcp_seq_num + 1 
        except socket.timeout as e:
            print e
            return
        finally:
            self.close()

        #unpack, check syn-ack and update ack_num, seq_num
        #send ack
        # last_handshake = self.pack_tcp_segment(flag=ACK)

    def close(self):
        #TODO: gracefully close down.
        # 1. Server initiates close.
        # 2. Client initiates close.
        self.rsocket.close()

    def unpack_ip_datagram(self, datagram):
        '''
        Paser IP datagram
        '''
        # print len(datagram)
        hdr_fields = struct.unpack(IP_HDR_FMT, datagram[:20])
        ip_header_size = struct.calcsize(IP_HDR_FMT)
        ip_ver_ihl = hdr_fields[0] 
        ip_ihl = ip_ver_ihl - (4 << 4)

        if ip_ihl > 5: 
            opts_size = (self.ip_ihl - 5) * 4 
            ip_header_size += opts_size 
        
        ip_headers = datagram[:ip_header_size]
        
        data = datagram[ip_header_size:hdr_fields[2]] 
        ip_check = checksum(ip_headers) 

        return IPDatagram(ip_daddr=socket.inet_ntoa(hdr_fields[-1]), ip_saddr=socket.inet_ntoa(hdr_fields[-2]),
            ip_frag_off=hdr_fields[4], ip_id=hdr_fields[3], ip_tlen=hdr_fields[2], ip_check=ip_check, data=data)


    def unpack_tcp_segment(self, segment):
        '''
        Parse TCP segment
        '''
        tcp_header_size = struct.calcsize(TCP_HDR_FMT)
        hdr_fields = struct.unpack(TCP_HDR_FMT, segment[:tcp_header_size])
        tcp_source = hdr_fields[0] 
        tcp_dest = hdr_fields[1] 
        tcp_seq = hdr_fields[2] 
        tcp_ack_seq = hdr_fields[3] 
        tcp_doff_resvd = hdr_fields[4] 
        tcp_doff = tcp_doff_resvd >> 4  # get the data offset 
        tcp_adwind = hdr_fields[6] 
        tcp_urg_ptr = hdr_fields[7] 
        # parse TCP flags 
        tcp_flags = hdr_fields[5] 
        # process the TCP options if there are 
        # currently just skip it 
        if tcp_doff > 5: 
            opts_size = (tcp_doff - 5) * 4 
            tcp_header_size += opts_size 
        
        # tcp_headers = segment[:tcp_header_size] 
        # get the TCP data 
        data = segment[tcp_header_size:] 
        # compute the checksum of the recv packet with psh 
        tcp_check = self._tcp_check(segment) 

        return TCPSeg(tcp_seq=tcp_seq, tcp_source=tcp_source, tcp_dest=tcp_dest, tcp_ack_seq=tcp_ack_seq,
            tcp_adwind=tcp_adwind, tcp_flags=tcp_flags, tcp_check=tcp_check, data=segment[tcp_header_size:])

    def _tcp_check(self, payload):
        # pseudo header fields
        source_address = socket.inet_aton(self.local_host)
        dest_address = socket.inet_aton(self.remote_host)
        placeholder = 0
        protocol = socket.IPPROTO_TCP
        tcp_length = len(payload)
         
        psh = struct.pack(PSH_FMT, source_address , dest_address , placeholder , protocol , tcp_length);
        psh = psh + payload;

        return checksum(psh)

    def recv_ack(self):
        #TODO: timeout retransmission.
        tcp_seg = self.recv()
        if tcp_seg.flags in (SYN_ACK, ACK):
            # self.tcp_ack_num = tcp_seg.tcp_seq
            # self.tcp_seq_num = tcp_seg.tcp_ack_seq
            return tcp_seg
        return None


def main():
    s = MyTCPSocket()
    s.connect(host='4.53.56.109', port=80)

if __name__ == '__main__':
    main()