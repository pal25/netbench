import select
import time
import socket

# Error imports / sets
from errno import EINTR, EINPROGRESS, EALREADY, EWOULDBLOCK, EISCONN, \
				EINVAL, ENOTCONN, EBADF, ECONNRESET, ESHUTDOWN, EPIPE, \
				ECONNABORTED

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

	def run(cls, timeout = 0.0):
		paused = False
		while not paused:
			r = []; w = []; e = []
			for fd, obj in cls.socket_table.items():
				is_r = obj.readable()
				is_w = obj.writeable()

				if is_r:
					f.append(fd)
				if is_w:
					w.append(fd)
				if is_r or is_w:
					e.append(fd)
	
			if [] == r == w == e:
				time.sleep(timeout)
				continue

			try:
				r, w, e = select.select(r, w, e, timeout)
			except select.err, err:
				if err.args[0] != EINTR:
					raise
				else:
					return

			for fd in r:
				obj = map.get(fd)
				if obj is None:
					continue
				else:
					read(obj)

			for fd in w:
				obj = map.get(fd)
				if obj is None:
					continue
				else:
					write(obj)

			for fd in e:
				obj = map.get(fd)
				if obj is None:
					continue
				else:
					_exception(obj)

	def stop():
		paused = True

	def read(obj):
		try:
			obj.handle_read_event()
		except _reraised_exceptions:
			raise
		except:
			obj.handle_error()

	def write(obj):
		try:
			obj.handle_write_event()
		except _reraised_exceptions:
			raise
		except:
			obj.handle_error()

	def _exception(obj):
		try:
			obj.handle_except_event()
		except _reraised_exceptions:
			raise
		except:
			obj.handle_error()
	
class Dispatcher:
	"""Dispatcher is an abstract class which is the default implementation for
		a connection in the event loop.

	   	sock = The socket we are wrapping
		
		connecting = Socket State: in currently attempting to connect
			which will be handled by the handle_connect call
		
		connected = Socket State: socket connected successfully and the
			connection has been handled properly

		accepting = Socket State: the socket is listening for connections
	"""
	def __init__(self):
		self.sock = None
		self.addr = None
		self.connected = False
		self.connecting = False
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
			self.connected = True
			
			try:
				self.addr = sock.getpeername()
			except socket.error, err:
				if err.args[0] in (ENOTCONN, EINVAL):
					self.connected = False
			else:
				raise	

	def connect(self, address, port):
		self.connecting = True
		self.connected = False

		err = self.sock.connect_ex((address, port))
		if err in (EINPROGRESS, EALREADY, EWOULDBLOCK):
			self.addr = (address, port)
			return
		if err in (0, EISCONN):
			self.addr = (address, port)
			self.handle_connect_event()
		else:
			raise socket.error(err, _sockerror(err))

	def close(self):
		self.connected = False
		self.accepting = False
		self.connecting = False
		try:
			self.sock.close()
		except socket.error, err:
			if err.args[0] not in (ENOTCONN, EBADF):
				raise

	def send(self, data):
		try:
			result = self.sock.send(data)
			return result
		except socket.error, err:
			if err.args[0] == EWOULDBLOCOK:
				return 0
			elif err.args[0] in _disconnected:
				self.handle_close()
				return 0
			else:
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
			if err.args[0]  in _disconnected:
				self.handle_close()
				return ''
			else:
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

	def handle_connect(self):
		"""ABSTRACT FUNCTION

		The functions handles program logic pertaining for a socket 
		connecting. By default this function does nothing and should be
		overwritten.
		"""
		pass

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
	
	def handle_connect_event(self):
		"""Handles socket connections and makes sure there are not errors.
		This function SHOULD NOT be implemented as it hands the event off to
		handle_connect() for user implementation.
		"""	
		err = self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
		if err != 0:
			raise socket.error(err, _sockerror(err))
		self.handle_connect()
		self.connecting = False
		self.connected = True
	
	def handle_read_event(self):
		"""Handles read events and makes sure there are not errors.
		This function SHOULD NOT be implemented as it hands the event off to
		handle_read() for user implementation.
		"""	
		if self.accepting:
			self.handle_accept()
		elif not self.connected:
			if self.connecting:
				self.handle_connect_event()
			self.handle_read()
		else:
			self.handle_read()

	def handle_write_event(self):
		"""Handles write events and makes sure there are not errors.
		This function SHOULD NOT be implemented as it hands the event off to
		handle_write() for user implementation.
		"""
		if self.accepting:
			return
		
		if not self.connected:
			if self.connecting:
				self.handle_connect_event()
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
