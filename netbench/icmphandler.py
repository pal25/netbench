from dispatcher import Dispatcher
from packet import IP, ICMPHeader
from utils import _sockerror, getLocalIP
import eventloop
import socket
import urllib
import logging
import sys

class ICMPHandler(Dispatcher):
	def __init__(self, destaddr):
		Dispatcher.__init__(self)

		try:		
			sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
			self.set_socket(sock)
			self.srcaddr = (getLocalIP(), destaddr[1])
			self.destaddr = destaddr						
			self.bind(self.srcaddr)			
		except socket.error, err:
			log_str = 'Socket Error: %s' % _sockerror(err.args[0])
			logging.root.exception(log_str)
			sys.exit(-1)

		log_str = 'Setup ICMP Listener (addr=%s, port=%s)' % (self.srcaddr[0], str(self.srcaddr[1]))
		logging.root.info(log_str)

	def __repr__(self):
		return '<ICMPHandler: Addr=(%s, %s)>' % (self.srcaddr[0],str(self.srcaddr[1]))	

	def readable(self):
		return True

	def handle_read(self):
		logging.root.debug('Handling Read')
		data, addr = self.sock.recvfrom(4096)
		
		recvIP = IP.disassemble(data)
		recvICMP = ICMPHeader.disassemble(recvIP.data)
		retnIP = IP.disassemble(recvICMP.data)
		
		if retnIP.ident in eventloop.probes:
			eventloop.probes[retnIP.ident](recvICMP)	

	def handle_except(self):
		logging.root.debug('Handling Except')
		self.handle_close()

	def handle_close(self):
		logging.root.debug('Handling Close')
		eventloop.stop()
		self.close()
	
		
