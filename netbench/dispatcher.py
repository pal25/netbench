import socket
import logging
from eventloop import EventLoop
from utils import _sockerror

# Error imports / sets
from errno import EINTR, EINPROGRESS, EALREADY, EWOULDBLOCK, EISCONN, \
				EINVAL, ENOTCONN, EBADF, ECONNRESET, ESHUTDOWN, EPIPE, \
				ECONNABORTED, errorcode
	
class Dispatcher:
	"""Dispatcher is an abstract class which is the default implementation for
		a connection in the event loop.

	   	sock = The socket we are wrapping

		accepting = Socket State: the socket is listening for connections
	"""
	def __init__(self):
		self.sock = None
		self.addr = None
		self.accepting = False
		self.eventloop = EventLoop()

	# ==================================================================
	# SOCKET WRAPPERS
	#
	# These functions wrap socket functionionality.
	# These are called either form the application or the event loop.
	# ==================================================================	

	def set_socket(self, sock):
		"""SOCKET WRAPPER set_socket

		This function sets the socket for a given dispatcher. It will also
		try to set the socket to a non-blocking socket, and retreive the host name
		for the socket host.

		sock = The input socket
		"""
		if self.sock is None:
			sock.setblocking(0)
			self.sock = sock

	def listen(self, num):
		self.accepting = true
		if os.name == 'nt' and num > 5:
			num = 5
		return self.sock.listen(num)
	
	def bind(self, addr):
		self.addr = addr
		return self.sock.bind(addr)

	def accept(self):
		try:
			conn, addr = self.sock.accept()
		except TypeError:
			return None
		except socket.error as err:
			if err.args[0] in (EWOULDBLOCK, ECONNABORTED, EAGAIN):
				return None
			else:
				raise
		else:
			return conn, addr	

	def close(self):
		self.accepting = False
		try:
			if self.sock.fileno() in self.eventloop.socket_table:
				del self.eventloop.socket_table[self.sock.fileno()]			
			self.sock.close()
		except socket.error, err:
			if err.args[0] not in (ENOTCONN, EBADF):
				log_str = 'Error: %s' % _sockerror(err.args[0])
				logging.root.exception(log_str)

	def send(self, data):
		try:
			result = self.sock.send(data)
			return result
		except socket.error, err:
			log_str = 'Could not send data: %s' % _sockerror(err.args[0])
			logging.root.info(log_str)
			
			if err.args[0] == EWOULDBLOCOK:
				return 0
			elif err.args[0] in _disconnected:
				self.handle_close()
				return 0
			else:
				log_str = 'Error: %s' % _sockerror(err.args[0])
				logging.root.error(log_str)
				raise

	def recv(self, buffer_size):
		try:
			databuffer = self.socket.recv(buffer_size)
			if not databuffer:
				self.handle_close()
				return ''
			else:
				return databuffer
		except socket.error, err:
			log_str = 'Could not recv data: %s' % _sockerror(err.args[0])
			logging.root.info(log_str)

			if err.args[0]  in _disconnected:
				self.handle_close()
				return ''
			else:
				log_str = 'Error: %s' % _sockerror(err.args[0])
				logging.root.error(log_str)
				raise

	# ==================================================================
	# ABSTRACT FUNCTIONS
	#
	# These should be overwritten by the application.
	# These functions have minimal functionality.
	# ==================================================================
		
	def readable(self):
		"""ABSTRACT FUNCTION
		
		This function gives the application the ability to set when a read event
		can occur. By default sockets are always unreadable for safety. This
		should be overwritten.
		"""
		return False

	def writeable(self):
		"""ABSTRACT FUNCTION
	
		This function gives the application the ability to set when a write event
		can occur. By default sockets are always unreadable for safety. This
		should be overwritten."""
		return False

	def handle_read(self):
		"""ABSTRACT FUNCTION

		The functions handles program logic pertaining for a socket 
		reading. By default this function does nothing and should be
		overwritten.
		"""
		pass

	def handle_write(self):
		"""ABSTRACT FUNCTION

		The functions handles program logic pertaining for a socket 
		writing. By default this function does nothing and should be
		overwritten.
		"""
		pass
		
	def handle_except(self):
		"""ABSTRACT FUNCTION

		The functions handles program logic pertaining for a socket 
		errors. By default this function does nothing and should be
		overwritten.
		"""
		self.handle_close()

	def handle_close(self):
		"""ABSTRACT FUNCTION

		The functions handles program logic pertaining for a socket 
		closing. By default this function does nothing and should be
		overwritten.
		"""
		self.close()

	def handle_accept(self):
		"""ABSTRACT FUNCTION

		The functions handles program logic pertaining for a socket 
		accepting. By default this function does nothing and should be
		overwritten.
		"""
		pass

	# ==================================================================
	# EVENT WRAPPERS
	#
	# These functions SHOULD NOT be overwritten.
	# These functions handle the logic to make sure there are no errors.
	# ==================================================================	
	def handle_read_event(self):
		"""Handles read events and makes sure there are not errors.
		This function SHOULD NOT be implemented as it hands the event off to
		handle_read() for user implementation.
		"""	
		if self.accepting:
			self.handle_accept()
		else:
			self.handle_read()

	def handle_write_event(self):
		"""Handles write events and makes sure there are not errors.
		This function SHOULD NOT be implemented as it hands the event off to
		handle_write() for user implementation.
		"""
		if self.accepting:
			return
		
		self.handle_write()

	def handle_except_event(self):
		"""Handles exception events and makes sure there are not errors.
		This function SHOULD NOT be implemented as it hands the event off to
		handle_except() for user implementation.
		"""
		err = self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
		if err != 0:
			self.handle_close()
		else:
			self.handle_except()		
