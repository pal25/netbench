from dispatcher import EventLoop, Dispatcher, _sockerror
from packet import IP, Datagram, ICMPHeader
import socket
import urllib
import logging
import os, sys

class UDPProbe(Dispatcher):
	def __init__(self, destaddr, callback):
		Dispatcher.__init__(self)
		self.callback = callback		

		self.ready = True
		self.max_ttl = 16
		self.current_ttl = 16
		self.min_ttl = 0
		
		try:		
			sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
			sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)						
			self.set_socket(sock)		
		except socket.error, err:
			if _sockerror(err.args[0]) == 'EPERM':
				logging.root.error('You need sudo privilages to use raw sockets')			
			else:
				log_str = 'Socket Error: %s' % _sockerror(err.args[0])
				logging.root.error(log_str)
			sys.exit(-1)

		# Hacky but if we're behind a NAT it's hard to find otherwise...		
		ip = (urllib.urlopen('http://automation.whatismyip.com/n09230945.asp').read())
		self.srcaddr = (ip, destaddr[1])

		# Setup the IP/UDP packets for sending.		
		self.datagram = Datagram(self.srcaddr[0],destaddr[0],self.srcaddr[1],destaddr[1],'')		
		self.packet = IP(socket.IPPROTO_UDP,self.srcaddr[0],destaddr[0],self.datagram,ttl=self.max_ttl)
		log_str = 'Setup UDP socket (srcaddr=%s, srcport=%s) (destaddr=%s, destport=%s)' % (str(self.srcaddr[0]), str(self.srcaddr[1]), destaddr[0], str(destaddr[1]))
		logging.root.debug(log_str)

		self.destaddr = destaddr

	def __repr__(self):
		return '<UDPProbe: Addr=(%s, %s), TTL=%s>' % (self.destaddr[0],str(self.destaddr[1]),self.max_ttl)

	def binary_search(self, data):
		"""Binary Search takes raw packet data, and searches for the proper number
		of hops to a particular router.

		data = the raw ip packet
		"""
		icmp = ICMPHeader.disassemble(data)
		
		if icmp.type == 3:
			self.max_ttl = self.current_ttl - 1
			log_str = 'TTL Too High'
			logging.root.info(log_str)
		elif icmp.type == 11:
			self.min_ttl = self.max_ttl + 1
			self.max_ttl = self.max_ttl * 2

			log_str = 'TTL Too Low'
			logging.root.info(log_str)
		else:
			log_str = 'Unknown ICMP Type=%d, Code=%d' % (icmp.type, icmp.code)
			logging.root.info(log_str)

		temp = self.current_ttl		
		self.current_ttl = self.min_ttl + ((self.max_ttl - self.min_ttl) / 2)


		if temp == self.current_ttl:
			print 'Found ttl', self.current_ttl
			self.callback()
		else:
			self.packet.ttl = self.current_ttl
			self.packet.ident = self.packet.ident+1
			self.ready = True
			log_str = 'Changing to: (Max: %s,Current: % s,Min: %s)' % (self.max_ttl, self.current_ttl, self.min_ttl)
			logging.root.info(log_str)
		
	def writeable(self):
		"""See Dispatcher for details """
		return self.ready

	def handle_write(self):
		"""See Dispatcher for details """
		logging.root.debug('Handling Write: ID=%d' % self.packet.ident)
		self.sock.sendto(self.packet.getdata, self.destaddr)
		self.ready = False
		
	def handle_except(self):
		"""See Dispatcher for details """
		logging.root.debug('Handling Except')
		self.handle_close()

	def handle_close(self):
		"""See Dispatcher for details """
		logging.root.debug('Handling Close')
		self.close()
