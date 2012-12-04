from dispatcher import Dispatcher
from packet import IP, Datagram, ICMPHeader
from utils import _sockerror, getLocalIP
from eventloop import EventLoop 
import socket
import logging
import os, sys, time

class UDPProbe(Dispatcher):
	def __init__(self, destaddr, output=None):
		Dispatcher.__init__(self)
		
		self.eventloop = EventLoop()
		
		self.starttime = None
		self.output = output

		self.ready = True
		self.max_ttl = 16
		self.current_ttl = 16
		self.min_ttl = 0
		self.ident = -1
		
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

	def binary_search(self, icmp, ident, finishtime):
		"""Binary Search takes raw packet data, and searches for the proper number
		of hops to a particular router.

		data = the raw ip packet
		"""
		if self.ident == ident:
			if icmp.type == 3:
				ip = IP.disassemble(icmp.data)
				ttl = self.current_ttl - ip.ttl + 1
				rtt = finishtime - self.starttime
				
				log_str = '%s: HOPS=%d, RTT=%d' % (self.destaddr[0], ttl, rtt)
				logging.root.info(log_str)
				if self.output:
					self.output.write('%s, %d, %d' % (self.destaddr[0], ttl, rtt))
				
				self.handle_close()
			elif icmp.type == 11:
				logging.root.debug('TTL Estimate Too Low')
				self.current_ttl = self.current_ttl*2
				self.create_packet()
				log_str = 'Changing TTL: %s' % self.current_ttl
				logging.root.info(log_str)
			else:
				log_str = 'Unknown ICMP Type=%d, Code=%d' % (icmp.type, icmp.code)
				logging.root.info(log_str)
				self.current_ttl = self.current_ttl*2
				self.create_packet()
				log_str = 'Changing TTL: %s' % self.current_ttl
				logging.root.info(log_str)
			
	def create_packet(self):
		if self.ident in self.eventloop.probes:
			logging.root.debug('Removing probe ID=%d' % self.ident)
			del self.eventloop.probes[self.ident] #Remove the old packet
		
		if self.current_ttl > 128:
			logging.root.info('Packets cannot reach server')
			self.handle_close()
			return
		else:
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
			
			self.ident = ident	
			self.packet = packet
			self.starttime = 0
			self.finsihtime = 0	
			self.ready = True
		
	def writeable(self):
		"""See Dispatcher for details """
		return self.ready

	def handle_write(self):
		"""See Dispatcher for details """
		logging.root.debug('Handling Write: ID=%d' % self.ident)
		self.starttime = int(round(time.time()*1000))
		self.sock.sendto(self.packet.getdata, self.destaddr)
		
		self.ready = False
		
	def timeout(self):
		self.current_ttl = self.current_ttl*2
		logging.root.debug('ID=%s: Timeout/Increasing TTL %d' % (self.ident, self.current_ttl))
			
		self.create_packet()
		
	def handle_except(self):
		"""See Dispatcher for details """
		logging.root.debug('Handling Except')
		self.handle_close()

	def handle_close(self):
		"""See Dispatcher for details """
		logging.root.debug('Handling Close')
		if self.ident in self.eventloop.probes:
			logging.root.debug('Removing probe ID=%d' % self.ident)
			del self.eventloop.probes[self.ident] #Remove the old packet
		self.close()
