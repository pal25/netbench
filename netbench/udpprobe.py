from dispatcher import Dispatcher
from packet import IP, Datagram, ICMPHeader
from utils import _sockerror, getLocalIP
from eventloop import EventLoop 
import socket
import logging
import os, sys

class UDPProbe(Dispatcher):
	def __init__(self, destaddr):
		Dispatcher.__init__(self)
		
		self.eventloop = EventLoop()	

		self.ready = True
		self.max_ttl = 16
		self.current_ttl = 16
		self.min_ttl = 0
		self.idents = {}
		
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
		
		self.destaddr = destaddr
		self.srcaddr = (getLocalIP(), destaddr[1])
		
		self.create_packet()

		log_str = 'Setup UDP socket (srcaddr=%s, srcport=%s) (destaddr=%s, destport=%s)' % (str(self.srcaddr[0]), str(self.srcaddr[1]), self.destaddr[0], str(self.destaddr[1]))
		logging.root.info(log_str)

	def __repr__(self):
		return '<UDPProbe: Addr=(%s, %s), TTL=%s>' % (self.destaddr[0],str(self.destaddr[1]),self.max_ttl)

	def binary_search(self, icmp, ident):
		"""Binary Search takes raw packet data, and searches for the proper number
		of hops to a particular router.

		data = the raw ip packet
		"""
		
		if icmp.type == 3:
			self.max_ttl = self.current_ttl - 1
			log_str = 'TTL Estimate Too High'
			logging.root.debug(log_str)
		elif icmp.type == 11:
			self.min_ttl = self.max_ttl + 1
			self.max_ttl = self.max_ttl * 2
			log_str = 'TTL Estimare Too Low'
			logging.root.debug(log_str)
		else:
			log_str = 'Unknown ICMP Type=%d, Code=%d' % (icmp.type, icmp.code)
			logging.root.info(log_str)

		temp = self.current_ttl		
		self.current_ttl = self.min_ttl + ((self.max_ttl - self.min_ttl) / 2)

		if self.min_ttl >= self.max_ttl:
			log_str = 'Found TTL: %d' % self.current_ttl
			logging.root.info(log_str)
			self.eventloop.stop()
		else:
			self.create_packets()
			log_str = 'Changing TTL: (Max:%s,Current:%s,Min:%s)' % (self.max_ttl, self.current_ttl, self.min_ttl)
			logging.root.info(log_str)
			
	def create_packet(self):
		for i in xrange(0,3):
			ident = self.eventloop.add_callback(self.binary_search)
			
			msg = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ\x5b\x5c\x5d\x5e\x5f'
			# Setup the IP/UDP packets for sending.		
			datagram = Datagram(self.srcaddr[0],
				self.destaddr[0],
				self.srcaddr[1],
				self.destaddr[1],
				msg)		
		
			packet = IP(socket.IPPROTO_UDP,
				self.srcaddr[0],
				self.destaddr[0],
				datagram,
				ttl=self.current_ttl,
				ident = ident)
				
			self.idents[ident] = (packet, True, 0, 0)	
			self.ready = True
		
	def writeable(self):
		"""See Dispatcher for details """
		return self.ready

	def handle_write(self):
		"""See Dispatcher for details """
		for ident in self.idents:
			data = self.idents[ident]
			if data[1] is True:
				logging.root.debug('Handling Write: ID=%d' % ident)
				self.sock.sendto(data[0].getdata, self.destaddr)
				self.idents[ident] = (data[0], False, 0, 0)
		
		self.ready = False
		
	def handle_except(self):
		"""See Dispatcher for details """
		logging.root.debug('Handling Except')
		self.handle_close()

	def handle_close(self):
		"""See Dispatcher for details """
		logging.root.debug('Handling Close')
		self.eventloop.stop()
		self.close()
