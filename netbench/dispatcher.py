import select
import time
import socket
import logging

# Error imports / sets
from errno import EINTR, EINPROGRESS, EALREADY, EWOULDBLOCK, EISCONN, \
				EINVAL, ENOTCONN, EBADF, ECONNRESET, ESHUTDOWN, EPIPE, \
				ECONNABORTED, errorcode

_reraised_exceptions = (KeyboardInterrupt, SystemExit)
_disconnected = (ECONNRESET, ENOTCONN, ESHUTDOWN, ECONNABORTED, EPIPE, EBADF)

def _sockerror(err):
	"""Helper function that determines if the socket error has a name to
	return to the user if the error occurs
	"""
	try:
		return os.strerror(err)
	except (ValueError, OverflowError, NameError):
		if err in errorcode:
			return errorcode[err]
		return "Unknown error %s" %err

class EventLoop(object):
	"""EventLoop is a singleton class that handles non-blocking socket 
		operations for ALL dispatchers

		socket_table = the hashtable that stores socket file descriptors and the 
		dispatcher that is handling that socket
	"""
	_instance = None
	socket_table = {}

	def __new__(cls):
		if not cls._instance:
			cls._instance = super(EventLoop, cls).__new__(cls)
		return cls._instance
	
	def add_dispatcher(cls, obj):
		fd = obj.sock.fileno()
		if fd not in cls.socket_table:
			cls.socket_table[fd] = obj
	
		log_str = 'Adding dispatcher: %s' % obj
		logging.root.info(log_str)

	def run(cls, timeout = 0.0):
		paused = False
		while not paused and cls.socket_table:
			r = []; w = []; e = []
			for fd, obj in cls.socket_table.items():
				is_r = obj.readable()
				is_w = obj.writeable()

				if is_r:
					r.append(fd)
				if is_w:
					w.append(fd)
				if is_r or is_w:
					e.append(fd)
	
			if [] == r == w == e:
				time.sleep(timeout)
				continue

			try:
				r, w, e = select.select(r, w, e, timeout)
			except select.error, err:
				log_str = 'Error: %s' % err.args[0]
				logging.root.error(log_str)

				if err.args[0] != EINTR:
					raise
				else:
					return

			for fd in r:
				obj = cls.socket_table.get(fd)
				if obj is None:
					continue
				else:
					cls.read(obj)

			for fd in w:
				obj = cls.socket_table.get(fd)
				if obj is None:
					continue
				else:
					cls.write(obj)

			for fd in e:
				obj = cls.socket_table.get(fd)
				if obj is None:
					continue
				else:
					cls._exception(obj)

	def stop():
		paused = True

	def read(cls, obj):
		try:
			obj.handle_read_event()
		except _reraised_exceptions:
			logging.root.error('Read error')
			raise
		except:
			obj.handle_except()

	def write(cls, obj):
		try:
			obj.handle_write_event()
		except _reraised_exceptions:
			logging.root.error('Write error')
			raise
		except:
			obj.handle_except()

	def _exception(cls, obj):
		try:
			obj.handle_except_event()
		except _reraised_exceptions:
			logging.root.error('Exception error')
			raise
		except:
			obj.handle_except()
	
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

	# ==================================================================
	# SOCKET WRAPPERS
	#
	# These functions wrap socket functionionality.
	# These are called either form the application or the event loop.
	# ==================================================================	

	def set_socket(self, sock):
		if self.sock is None:
			sock.setblocking(0)
			self.sock = sock
			
			try:
				self.addr = sock.getpeername()
			except socket.error, err:
				log_str = 'Unable to auto-obtain addr: %s' % _sockerror(err.args[0])
				logging.root.info(log_str)
				
				if err.args[0] not in (ENOTCONN, EINVAL):
					log_str = 'Error: %s' % _sockerror(err)
					logging.root.error(log_str)
					raise

	def listen(self, num):
		self.accepting = true
		if os.name == 'nt' and num > 5:
			num = 5
		return self.sock.listen(num)
	
	def bind(self, addr):
		self.addr = addr
		return self.sock.bind(self.addr)

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
			del EventLoop.socket_table[self.sock.fileno()]			
			self.sock.close()
		except socket.error, err:
			if err.args[0] not in (ENOTCONN, EBADF):
				log_str = 'Error: %s' % _sockerror(err.args[0])
				logging.root.error(log_str)
				raise

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
