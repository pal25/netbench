import logging
import random
import select
import time
import socket
import time
from utils import _sockerror, _reraised_exceptions, _disconnected

class Singleton(type):
	_instances = {}
	def __call__(cls, *args, **kwargs):
		if cls not in cls._instances:
			cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
		return cls._instances[cls]

class EventLoop:
	__metaclass__ = Singleton
	
	def __init__(self):
		self.socket_table = {} 		# Holds socket connections to be polled
		self.probes = {}			# Adds probes to callback
		self.paused = None			# Status of the eventloop
		self.randid = random.getrandbits(14) << 2
		
	def add_callback(self, callback):	
		self.randid = self.randid + 1
		self.probes[self.randid] = callback
	
		log_str = 'Adding Callback: id=%d' % self.randid
		logging.root.info(log_str)
			
		return self.randid
		
	def add_dispatcher(self, obj):
		fd = obj.sock.fileno()
		if fd not in self.socket_table:
			self.socket_table[fd] = obj
			log_str = 'Adding dispatcher: %s' % obj
			logging.root.info(log_str)
	
	def run(self, timeout = 0.0):
		self.paused = False
		while not self.paused and len(self.probes) > 0:
			r = []; w = []; e = []
			for fd, obj in self.socket_table.items():
				
				if hasattr(obj, 'starttime') and obj.starttime:
					if (time.time() - obj.starttime) > timeout:
						obj.timeout()
				
				obj.sock.settimeout(timeout)
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
				obj = self.socket_table.get(fd)
				if obj is None:
					continue
				else:
					self.read(obj)
	
			for fd in w:
				obj = self.socket_table.get(fd)
				if obj is None:
					continue
				else:
					self.write(obj)
	
			for fd in e:
				obj = self.socket_table.get(fd)
				if obj is None:
					continue
				else:
					self._exception(obj)
	
	def stop(self):
		logging.root.info('Stopping the EventLoop')
		self.paused = True
		
	def read(self, obj):
		try:
			obj.handle_read_event()
		except _reraised_exceptions:
			logging.root.error('Read error')
			raise
		except:
			logging.exception('Read error')
			obj.handle_except()
	
	def write(self, obj):
		try:
			obj.handle_write_event()
		except _reraised_exceptions:
			logging.root.error('Write error')
			raise
		except Exception, err:
			logging.exception('Write error')
			obj.handle_except()
	
	def _exception(self, obj):
		try:
			obj.handle_except_event()
		except _reraised_exceptions:
			logging.root.error('Exception error')
			raise
		except:
			obj.handle_except()
	
