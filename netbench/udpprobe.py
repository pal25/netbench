from dispatcher import Dispatcher, _sockerror
from packet import IP, Datagram, ICMPHeader
import socket
import logging
import os

class UDPProbe(Dispatcher):
	def __init__(self, destaddr):
		Dispatcher.__init__(self)
		
		self.ready = True
		self.max_ttl = 16
		self.min_ttl = 8
		#self.id = os.urandom(1)
		
		srcaddr = (socket.gethostbyname('192.168.0.10'), destaddr[1])
		
		self.datagram = Datagram(srcaddr[0], 
								destaddr[0], 
								srcaddr[1], 
								destaddr[1], 
								'')		

		self.packet = IP(socket.IPPROTO_UDP, 
						srcaddr[0], 
						destaddr[0], 
						self.datagram, 
						ttl=self.max_ttl)
		
		try:		
			sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
			sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)						
			self.set_socket(sock)		
		except socket.error, err:
			log_str = 'Socket Error: %s' % _sockerror(err.args[0])
			logging.root.error(log_str)

		log_str = 'Setup UDP socket (addr=%s, port=%s)' % (destaddr[0], str(destaddr[1]))
		logging.root.debug(log_str)

		self.destaddr = destaddr
		self.srcaddr = srcaddr

	def __repr__(self):
		return '<UDPProbe: Addr=(%s, %s), TTL=%s>' % (self.destaddr[0],str(self.destaddr[1]),self.max_ttl)

	def binary_search(self, data):
		icmp = ICMPHeader.disassemble(data)
		
		if icmp.type == 3:
			self.max_ttl = self.min_ttl + ((self.max_ttl-1) - self.min_ttl) / 2

			log_str = 'TTL High: (Max: %s, Min %s (TTL))' % (self.max_ttl, self.min_ttl)
			logging.root.info(log_str)

		elif icmp.type == 11:
			self.max_ttl = self.max_ttl * 2

			log_str = 'TTL Low: (Max: %s, Min: %s (TTL))' % (self.max_ttl, self.min_ttl)
			logging.root.info(log_str)

		else:
			log_str = 'Unknown ICMP Type=%d, Code=%d' % (icmp.type, icmp.code)
			logging.root.info(log_str)


		self.packet.ttl = self.max_ttl
		self.packet.ident = self.packet.ident+1
		self.ready = True
		
	def writeable(self):
		return self.ready

	def handle_write(self):
		logging.root.debug('Handling Write: ID=%d' % self.packet.ident)
		self.sock.sendto(self.packet.getdata, self.destaddr)
		self.ready = False
		
	def handle_except(self):
		logging.root.debug('Handling Except')
		self.handle_close()

	def handle_close(self):
		logging.root.debug('Handling Close')
		self.close()
