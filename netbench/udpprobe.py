from dispatcher import Dispatcher
import socket
import logging

class UDPProbe(Dispatcher):
	def __init__(self, addr, port):
		Dispatcher.__init__(self)

		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, 16)
		
		log_str = 'Setup UDP socket (addr=%s, port=%s)' % (addr, str(port))
		logging.root.debug(log_str)

		self.set_socket(sock)
		self.connect(addr, port)

	def readable(self):
		#logging.root.debug('Checking Readable')
		return False

	def writeable(self):
		#logging.root.debug('Checking Writeable')
		return False

	def handle_connect(self):
		logging.root.debug('Handling Connect')
		pass

	def handle_read(self):
		logging.root.debug('Handling Read')
		pass

	def handle_write(self):
		logging.root.debug('Handling Write')
		pass
		
	def handle_except(self):
		logging.root.debug('Handling Except')
		self.handle_close()

	def handle_close(self):
		logging.root.debug('Handling Close')
		self.close()

	def handle_accept(self):
		logging.root.debug('Handling Accept')
		pass
