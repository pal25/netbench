import socket
import os
import logging

# Error imports / sets
from errno import EINTR, EINPROGRESS, EALREADY, EWOULDBLOCK, EISCONN, \
				EINVAL, ENOTCONN, EBADF, ECONNRESET, ESHUTDOWN, EPIPE, \
				ECONNABORTED, errorcode

_reraised_exceptions = (KeyboardInterrupt, SystemExit)
_disconnected = (ECONNRESET, ENOTCONN, ESHUTDOWN, ECONNABORTED, EPIPE, EBADF)

def _sockerror(err):
	"""HELPER FUNCTION 
	
	Determines if the socket error has a name assigned to it.
	
	input: Error code to look up
	return: Stringified version of socket error 
	"""
	try:
		return os.strerror(err)
	except (ValueError, OverflowError, NameError):
		if err in errorcode:
			return errorcode[err]
		return "Unknown error %s" %err
		
def getLocalIP():
	"""HELPER FUNCTION
	
	Extremely hacky way to retrieve host's IP even if on a NAT.
	
	return: String version of IP address to the host.
	"""
	local_addr = '127.0.0.1'
	try:
		import urllib2
		local_addr = urllib2.urlopen('http://prod-snscholar.case.edu').read()
	except urllib2.URLError, err:
		log_str = 'URLLib2 Err: %s' % (err[0])
		logging.root.warning(log_str)
	
	log_str = 'Local IP = %s' % local_addr
	logging.root.debug(log_str)
	return local_addr
