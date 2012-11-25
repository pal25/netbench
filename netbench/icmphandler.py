from dispatcher import Dispatcher, _sockerror
import socket
import logging

class ICMPHandler(Dispatcher):
	def __init__(self, callback):
		Dispatcher.__init__(self)

		try:		
			sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
			self.set_socket(sock)		
			self.addr = ('192.168.0.10', int(0))			
			#self.addr = socket.gethostbyname(socket.gethostname()), int(0)		
			self.bind(self.addr)			
		except socket.error, err:
			log_str = 'Socket Error: %s' % _sockerror(err.args[0])
			logging.root.error(log_str)	

		log_str = 'Setup ICMP Listener (addr=%s, port=%s)' % (self.addr[0], str(self.addr[1]))
		logging.root.debug(log_str)

	def __repr__(self):
		return '<ICMPHandler: Addr=(%s, %s)>' % (self.addr[0],str(self.addr[1]))	

	def readable(self):
		return False

	def handle_read(self):
		logging.root.debug('Handling Read')
		pass

	def handle_except(self):
		logging.root.debug('Handling Except')
		self.handle_close()

	def handle_close(self):
		logging.root.debug('Handling Close')
		self.close()
	
		
