import struct
from util import checksum
TCP_HDR_FMT = '!HHLLBBHHH'
PSH_FMT = '!4s4sBBH'


class TCPSegment(object):

	"""docstring for TCPSegment"""

	def __init__(self, local_host, remote_host, local_port=0, remote_port=0, tcp_seq_num=0, tcp_ack_num=0, flag=0, tcp_window=5840, payload=''):
        # tcp header fields
        self.local_host = local_host
        self.remote_host = remote_host
        self.tcp_source = local_port   # source port
        self.tcp_dest = remote_port   # destination port
        self.tcp_seq = tcp_seq_num
        self.tcp_ack_seq = tcp_ack_num
        self.tcp_doff = 5  # 4 bit field, size of tcp header, 5 * 4 = 20 bytes
        # maximum allowed window size
        self.tcp_window = socket.htons(tcp_window)
        self.tcp_check = 0
        self.tcp_urg_ptr = 0
        self.tcp_offset_res = (tcp_doff << 4) + 0
        self.tcp_flags = flag
        self.payload = payload
        self.raw = ''

    def pack(self):
        tcp_header = struct.pack(TCP_HDR_FMT, self.tcp_source, self.tcp_dest, self.tcp_seq, self.tcp_ack_seq, self.tcp_offset_res, self.tcp_flags,  self.tcp_window, self.tcp_check, self.tcp_urg_ptr)
         
        # pseudo header fields
        source_address = socket.inet_aton(self.local_host)
        dest_address = socket.inet_aton(self.remote_host)
        placeholder = 0
        protocol = socket.IPPROTO_TCP
        tcp_length = len(tcp_header) + len(self.payload)
         
        psh = struct.pack(PSH_FMT, source_address , dest_address , placeholder , protocol , tcp_length);
        psh = psh + tcp_header + self.payload;
        
        tcp_check = checksum(psh)
        # print tcp_checksum

        tcp_header = struct.pack(TCP_HDR_FMT[:-2], self.tcp_source, self.tcp_dest, self.tcp_seq, self.tcp_ack_seq, self.tcp_offset_res, self.tcp_flags, self.tcp_window) + struct.pack('H' , self.tcp_check) + struct.pack('!H' , self.tcp_urg_ptr)

        self.raw = tcp_header + self.payload

		
    def verify_checksum(self):
    	pass