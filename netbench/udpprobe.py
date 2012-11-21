from dispatcher import Dispatcher
import socket

class UDPProbe(Dispatcher):
	def __init__(self, addr, port):
		Dispatcher.__init__(self)

		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, 16)

		self.set_socket(sock)
		self.connect(addr, port)

	def readable(self):
		return False

	def writeable(self):
		return False

	def handle_connect(self):
		pass

	def handle_read(self):
		pass

	def handle_write(self):
		pass
		
	def handle_except(self):
		self.handle_close()

	def handle_close(self):
		self.close()

	def handle_accept(self):
		pass
