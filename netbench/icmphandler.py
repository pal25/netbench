from dispatcher import Dispatcher, _sockerror, EventLoop
from packet import IP, ICMPHeader
import socket
import urllib
import logging

class ICMPHandler(Dispatcher):
	def __init__(self, destaddr):
		Dispatcher.__init__(self)
		self.loop = EventLoop()
		self.destaddr = destaddr
		
		# Hacky but if we're behind a NAT it's hard to find otherwise...
		#ip = (urllib.urlopen('http://automation.whatismyip.com/n09230945.asp').read())
		ip = '127.0.0.1'		
		self.srcaddr = (ip, destaddr[1])

		try:		
			sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
			self.set_socket(sock)						
			self.bind(self.srcaddr)			
		except socket.error, err:
			log_str = 'Socket Error: %s' % _sockerror(err.args[0])
			logging.root.error(log_str)	

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
		self.loop.probe[retnIP.ident](recvICMP)	

	def handle_except(self):
		logging.root.debug('Handling Except')
		self.handle_close()

	def handle_close(self):
		logging.root.debug('Handling Close')
		self.loop.stop()
		self.close()
	
		
