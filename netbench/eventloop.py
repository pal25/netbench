import logging
import random
import select
import time
import socket
import sys #TODO: Get rid of this dependency
from utils import _sockerror, _reraised_exceptions, _disconnected

socket_table = {} 	# Holds socket connections to be polled
probes = {}			# Adds probes to callback
paused = None		# Status of the eventloop
	
def add_callback(callback):
	randid = random.getrandbits(16)
	while randid in probes:
		randid = random.getrandbits(16)
					
	probes[randid] = callback

	log_str = 'Adding Callback: id=%d' % randid
	logging.root.info(log_str)
		
	return randid
	
def add_dispatcher(obj):
	fd = obj.sock.fileno()
	if fd not in socket_table:
		socket_table[fd] = obj
	
	log_str = 'Adding dispatcher: %s' % obj
	logging.root.info(log_str)

def run(timeout = 0.0):
	paused = False
	while not paused:
		r = []; w = []; e = []
		for fd, obj in socket_table.items():
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
			obj = socket_table.get(fd)
			if obj is None:
				continue
			else:
				read(obj)

		for fd in w:
			obj = socket_table.get(fd)
			if obj is None:
				continue
			else:
				write(obj)

		for fd in e:
			obj = socket_table.get(fd)
			if obj is None:
				continue
			else:
				_exception(obj)

def stop():
	logging.root.info('Stopping the EventLoop')
	#paused = True
	sys.exit(0) #TODO: Get rid of this and back to paused
	
def read(obj):
	try:
		obj.handle_read_event()
	except _reraised_exceptions:
		logging.root.error('Read error')
		raise
	except:
		logging.exception('Read error')
		obj.handle_except()

def write(obj):
	try:
		obj.handle_write_event()
	except _reraised_exceptions:
		logging.root.error('Write error')
		raise
	except Exception, err:
		logging.exception('Write error')
		obj.handle_except()

def _exception(obj):
	try:
		obj.handle_except_event()
	except _reraised_exceptions:
		logging.root.error('Exception error')
		raise
	except:
		obj.handle_except()
