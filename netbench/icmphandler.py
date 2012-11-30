from dispatcher import Dispatcher, _sockerror
from packet import IP
import socket
import urllib
import logging

class ICMPHandler(Dispatcher):
	def __init__(self, destaddr, callback):
		Dispatcher.__init__(self)

		self.callback = callback
		self.destaddr = destaddr
		
		# Hacky but if we're behind a NAT it's hard to find otherwise...
		ip = (urllib.urlopen('http://automation.whatismyip.com/n09230945.asp').read())
		self.srcaddr = (ip, destaddr[1])

		try:		
			sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
			self.set_socket(sock)						
			self.bind(self.srcaddr)			
		except socket.error, err:
			log_str = 'Socket Error: %s' % _sockerror(err.args[0])
			logging.root.error(log_str)	

		log_str = 'Setup ICMP Listener (addr=%s, port=%s)' % (self.srcaddr[0], str(self.srcaddr[1]))
		logging.root.debug(log_str)

	def __repr__(self):
		return '<ICMPHandler: Addr=(%s, %s)>' % (self.srcaddr[0],str(self.srcaddr[1]))	

	def readable(self):
		return True

	def handle_read(self):
		logging.root.debug('Handling Read')
		data, addr = self.sock.recvfrom(1024)
		recvIP = IP.disassemble(data)
		self.callback(data[recvIP.header_length:recvIP.header_length+8])	

	def handle_except(self):
		logging.root.debug('Handling Except')
		self.handle_close()

	def handle_close(self):
		logging.root.debug('Handling Close')
		self.close()
	
		
