from dispatcher import Dispatcher, _sockerror
import socket
import logging

class UDPProbe(Dispatcher):
	def __init__(self, addr):
		Dispatcher.__init__(self)
		
		self.ready = True
		self.current_ttl = 16
		self.last_ttl = 8

		try:		
			#sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)		
			sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)					
			self.set_socket(sock)
			self.addr = addr		
		except socket.error, err:
			log_str = 'Socket Error: %s' % _sockerror(err.args[0])
			logging.root.error(log_str)

		log_str = 'Setup UDP socket (addr=%s, port=%s)' % (addr[0], str(addr[1]))
		logging.root.debug(log_str)

	def __repr__(self):
		return '<UDPProbe: Addr=(%s, %s), TTL=%s>' % (self.addr[0],str(self.addr[1]),self.current_ttl)

	def binary_search(self, high):
		if high:
			temp = self.current_ttl
			self.current_ttl = (self.current_ttl + self.last_ttl) / 2
			self.last_ttl = temp
		else:
			self.last_ttl = self.current_ttl
			self.current_ttl = self.last_ttl * 2

		sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, self.current_ttl)
		self.ready = True

	def writeable(self):
		return self.ready

	def handle_write(self):
		logging.root.debug('Handling Write')
		self.sock.sendto('test', self.addr)
		self.ready = False
		
	def handle_except(self):
		logging.root.debug('Handling Except')
		self.handle_close()

	def handle_close(self):
		logging.root.debug('Handling Close')
		self.close()
