import select
import time

from errno import EINTR

class EventLoop(object):
	"""EventLoop is a singleton class that handles non-blocking socket 
		operations for ALL dispatchers

		sockets = the hashtable that stores socket file descriptors and the 
		dispatcher that is handling that socket
	"""
	_instance = None
	sockets = {}

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(EventLoop, cls).__new__(cls)
        return cls._instance
	
	def add_dispatcher(obj):
		fd = obj.sock.fileno()
		if socket_list[fd] is None:
			socket_list[fd] = obj

	def run(timeout = 0.0):
		paused = False
		while sockets and not paused:
			r = []; w = []; e = []
			for fd, obj in sockets.items():
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
				return

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

	   	map = is a hashtable which contains all socket connections
	"""
	def __init__(self):
		self.sock = None
		self.connected = False

	def handle_read_event():
		pass

	def handle_write_event():
		pass

	def handle_except_event():
		pass		
