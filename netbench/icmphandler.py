from dispatcher import Dispatcher
from packet import IP, ICMPHeader
from utils import _sockerror, getLocalIP
from eventloop import EventLoop
import socket
import logging
import sys

class ICMPHandler(Dispatcher):
	def __init__(self, destaddr):
		Dispatcher.__init__(self)
		self.eventloop = EventLoop()

		self.destaddr = destaddr
		self.srcaddr = ('0.0.0.0', 1)

		try:		
			sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
			self.set_socket(sock)	
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
		
		if retnIP.ident in self.eventloop.probes:
			self.eventloop.probes[retnIP.ident](recvICMP, retnIP.ident)	

	def handle_except(self):
		logging.root.debug('Handling Except')
		self.handle_close()

	def handle_close(self):
		logging.root.debug('Handling Close')
		self.eventloop.stop()
		self.close()
	
		
