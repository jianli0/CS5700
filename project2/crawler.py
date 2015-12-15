import socket
import sys
import re
import argparse
import select
from bs4 import BeautifulSoup


parser = argparse.ArgumentParser() 
parser.add_argument('username', type=str, help='username') 
parser.add_argument('password', type=str, help='password') 

#HTTP client settings
MAX_READ_SIZE = 4096
STATUS_FOUND = b'302'
STATUS_OK = b'200'
STATUS_REDIRECT = b'301'
STATUS_NOTFOUND = b'404'
STATUS_SERVERERR = b'500'
STATUS_FORBIDDEN = b'403'


lrule = re.compile(b'Location: (\w+:\/\/.{0,128})')
drule = re.compile('\/fakebook\/.{0,40}')

class Worker(object):
    """
    Worker wraps a TCP socket and its current reading, writing states.
    This class is designed for supporting asynchronous pattern.
    `state` indicates the current mode of this Worker.
        0 - write mode(default).
        1 - read mode.
        2 - error.
    """

    def __init__(self, host, port, no):
        # self.crawler = crawler
        self.no = no
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect()
        # Bytes buffers
        # self.last_read_len = -1
        self.read_buf = None
        self.read_callback = None
        self.write_buf = None
        # Error store
        self.error = None
        self.write_pos = -1
        self.state = 0
        self.target_url = ''

    def wants_read(self):
        return self.state == 1
    
    def wants_write(self):
        return self.state == 0

    def gets_error(self):
        return self.state == 2

    def read(self, callback=print):
        self.read_buf = bytearray()
        self.read_callback = callback
        self.handle_read()

    def write(self, target_url, buf):
        self.write_buf = buf
        self.target_url = target_url
        self.write_pos = 0
        self.handle_write()

    def handle_write(self):
        if self.write_buf:
            try:
                n = self.socket.send(self.write_buf)
                self.write_pos += n
                self.write_buf = self.write_buf[n:]
            except Exception as e:
                self.handle_error(e)
        else:
            self._on_write_done()

    def handle_read(self):
        try:
            data = self.socket.recv(MAX_READ_SIZE)
            self.read_buf.extend(data)
            if len(data) == 0 or self.read_buf.endswith(b'\r\n\r\n') or self.read_buf.endswith(b'</html>'):
                self._on_read_done()
        except Exception as e:
            self.handle_error(e)

    def reconnect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect()

    def connect(self):
        self.socket.connect((self.host, self.port))
        self.socket.setblocking(False)

    def _on_write_done(self):
        self.state = 1
        self.write_buf = None
        self.write_pos = -1

    def _on_read_done(self):
        self.state = 0
        # Extract links from HTML and put them into frontier.
        if self.read_callback:
            self.read_callback(self.target_url, self.read_buf)
        
        self.read_buf = None
        self.read_callback = None
        self.socket.close()
        self.reconnect()

    def handle_error(self, err):
        self.socket.close()
        self.reconnect()
        self.read_buf = None
        self.read_callback = None
        self.write_buf = None
        # Error store
        self.error = None
        self.write_pos = -1
        self.state = 0        

    def fileno(self):
        return self.socket.fileno()

    def __repr__(self):
        return "[WORKER %d]" % self.no


class Crawler(object):
    request = "GET {{url}} HTTP/1.1\r\n" + \
              "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n" + \
              "Host: {host}\r\n" + \
              "Cookie: {cookie}\r\n" + \
              "Connection: keep-alive\r\n" + \
              "User-Agent: KexiCrawler\r\n\r\n"
    
    def __init__(self, host, port, user=None, passwd=None, conn_num=100):
        self.flags = set()
        self.host = host
        self.port = port
        self.to_visit = set()
        self.visited = set()
        self.cookie = {}
        self.workers = [Worker(host, port, i) for i in range(100)]
        self.user = user
        self.passwd = passwd
    
    def start(self):
        retry = 0
        while not self.login(self.user, self.passwd) and retry < 5:
            retry += 1
        if retry >= 5:
            print("Username/Password incorrect")
            return

        cookie = "csrftoken=" + self.cookie['csrftoken'] +'; sessionid=' + self.cookie['sessionid']

        self.request = self.request.format(host=self.host, cookie=cookie)
        while len(self.flags) < 5:
            rlist = [worker for worker in self.workers if worker.wants_read()]
            wlist = [worker for worker in self.workers if worker.wants_write()]
            
            readables, writables, exceptions = select.select(rlist, wlist, [], 3)

            if readables: self.process_read(readables)
            if writables: self.process_write(writables)

            # print('to_visit: %d\nflags: %d\nvisited: %d' % (len(self.to_visit), len(self.flags), len(self.visited)))

        for flag in self.flags: print(flag)

    def process_write(self, writables):
        for worker in writables:
            if worker.write_pos >= 0:
                worker.handle_write()
            elif self.to_visit:
                target_url = self.to_visit.pop()
                worker.write(target_url, bytearray(self.request.format(url=target_url), 'ascii'))

    def process_read(self, readables):
        for worker in readables:
            if not worker.read_buf:
                worker.read(self.process_response)
            else:
                worker.handle_read()

    def process_response(self, target_url, resp):
        status_code = self.get_status_code(resp)
        if not status_code or status_code == STATUS_NOTFOUND or status_code == STATUS_FORBIDDEN:
            #Discard this url.
            self.visited.add(target_url)
        elif status_code == STATUS_REDIRECT:
            durl = lrule.search(resp).group(1)
            if durl not in self.to_visit and durl not in self.visited: self.to_visit.add(durl)
            self.visited.add(target_url)
        elif status_code == STATUS_SERVERERR:
            #Re-try this url.
            if target_url not in self.to_visit and target_url not in self.visited: self.to_visit.add(target_url)

        elif status_code == STATUS_OK:
            self.find_secret_flag(resp)
            self.visited.add(target_url)

            html = BeautifulSoup(resp, 'html.parser')
            
            for tag in html.find_all('a'):
                if tag['href'] and self.is_in_domain(tag['href']) and tag['href'] not in self.visited and tag['href'] not in self.to_visit:
                    self.to_visit.add(tag['href'])
    
    def find_secret_flag(self, resp):
        flagRule = re.compile(b'FLAG: (.{0,64})')
        flag = flagRule.search(resp)
        if flag: self.flags.add(flag.group(1).decode())
    

    def login(self, username, passwd):
        login_request = "POST http://fring.ccs.neu.edu/accounts/login/ HTTP/1.1\r\nHost: fring.ccs.neu.edu\r\nConnection: close\r\nContent-Length: {length}\r\nUser-Agent: kexi\r\nContent-Type: application/x-www-form-urlencoded\r\nCookie: csrftoken={csrftoken}; sessionid={sid}\r\n\r\n"
        get_login_page = b"GET /accounts/login/ HTTP/1.1\r\nHost: fring.ccs.neu.edu\r\nConnection: Keep-Alive\r\nUser-Agent: kexi\r\n\r\n"
        
        s = socket.socket()
        s.connect((self.host, self.port))
        s.sendall(get_login_page)
        resp = s.recv(MAX_READ_SIZE)

        csrfRule = re.compile(b'csrftoken=(\w+)')
        sidRule = re.compile(b'sessionid=(\w+)')
        csrftoken = csrfRule.search(resp).group(1)
        sessionid = sidRule.search(resp).group(1)
        
        formdata = "username={username}&password={passwd}&csrfmiddlewaretoken={csrf}&next=/fakebook/".format(username=username, passwd=passwd, csrf=csrftoken.decode())
        login_request = login_request.format(length=len(formdata), csrftoken=csrftoken.decode(), sid=sessionid.decode('ascii'))

        s.sendall(bytes(login_request+formdata, 'ascii'))
        resp = s.recv(MAX_READ_SIZE)
        s.close()

        if self.get_status_code(resp) == b'302':
            sessionid = sidRule.search(resp).group(1)
            self.cookie['sessionid'] = sessionid.decode()
            self.cookie['csrftoken'] = csrftoken.decode()
            self.to_visit.add(lrule.search(resp).group(1).decode())
            return True
        
        return False
    
    def get_status_code(self, resp):
        """Get HTTP status code from the response"""
        status = re.search(b"HTTP/1.1 (\d+)", resp)
        if status:
            code = status.group(1)
            return code
        return b''

    def is_in_domain(self, url):
        """
            Returns True if `url` is a relative path in the domain.
        """
        return drule.match(url) is not None

    def __repr__(self):
        return "[Crawler]"


if __name__ == '__main__':
    host = "fring.ccs.neu.edu"
    port = 80
    args = parser.parse_args() 
    username = args.username
    password = args.password
    crawler = Crawler(host, port, username, password)
    crawler.start()
    