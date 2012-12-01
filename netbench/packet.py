import socket
import struct
import logging
import array

def compute_checksum(data):
	if len(data) & 1:
		data = data + '\0'

	words = array.array('h', data)
	sum = 0
	for word in words:
		sum = sum + (word & 0xffff)
	hi = sum >> 16
	low = sum & 0xffff
	sum = hi + low
	sum = sum + (sum >> 16)
	return (~sum) & 0xffff
		
def parse_addr(addr):
	try:
		new_addr = socket.inet_aton(addr)
	except:
		addr = socket.gethostbyname(addr)
		try:
			new_addr = socket.inet_aton(addr)
		except ValueError:
			logging.exception('Error:')
			raise ValueError, 'Invalid address: %s' % addr

	return new_addr

class IP:
	def __init__(self,
				protocol,
				srcaddr,
				destaddr,				
				data,
				version=4,
				ihl=5,
				tos=0,
				total_length=0,
				ident=0,
				flags = 2,
				frag_off = 0,
				ttl=16,
				checksum=0):

		self.version = version
		self.tos = tos
		self.ihl = ihl
		self.header_length = ihl * 4
		self.ident = ident
		self.flags = flags
		self.frag_off = frag_off
		self.ttl = ttl
		self.checksum = checksum
		self.protocol = protocol
		self.srcaddr = parse_addr(srcaddr)
		self.destaddr = parse_addr(destaddr)
		self.data = data
		
		logging.root.debug('IP ID=%s' % ident)
		
		if total_length == 0:		
			self.total_length = self.header_length + self.data.total_length
		self.ip_header = None
	
	def assemble(self):		
		version_ihl = (self.version << 4) + self.ihl
		flags_frag_off = (self.flags << 13) + self.frag_off		
		
		self.ip_header = struct.pack('!BBHHHBBH', 
								version_ihl,
								self.tos,
								self.total_length,
								self.ident,
								flags_frag_off,
								self.ttl,
								self.protocol,
								self.checksum)

		self.ip_header = self.ip_header + self.srcaddr + self.destaddr

		if self.checksum == 0:
			self.checksum = compute_checksum(self.ip_header)
			self.assemble()

	@property
	def getdata(self):
		self.assemble()
		data = self.data.getdata
		return self.ip_header + data
	
	@classmethod	
	def disassemble(cls, recvdata):
		logging.root.debug('IP Length: %d', len(recvdata))

		version_ihl = struct.unpack('!B', recvdata[:1])[0]
		version = (version_ihl >> 4) & 0x0f
		ihl = version_ihl & 0x0f

		if ihl == 5: # No options specified
			tos, total_length, ident, flags_frag_off, ttl, protocol, checksum, \
			srcaddr, destaddr = struct.unpack('!BHHHBBH4s4s', recvdata[1:20])

			data = recvdata[20:]
			flags = (flags_frag_off & 0xe000) >> 13
			frag_off = flags_frag_off & 0x1fff
			srcaddr = socket.inet_ntoa(srcaddr)
			destaddr = socket.inet_ntoa(destaddr)

			return IP(protocol,srcaddr,destaddr,data,version,ihl,tos, \
			total_length, ident,flags,frag_off,ttl,checksum)
		
		else:
			logging.root.error('IP options header field not supported')
			pass

class Datagram:
	def __init__(self, 
				srcaddr, 
				destaddr, 
				srcport, 
				destport, 
				data, 
				header_length=8, 
				checksum=0):

		self.srcaddr = parse_addr(srcaddr)
		self.destaddr = parse_addr(destaddr)		
		self.srcport = srcport
		self.destport = destport
		self.data = data
		self.header_length = header_length
		self.checksum = checksum
	
		self.total_length = self.header_length + len(self.data)
		self.udp_header = None

	def assemble(self):
		self.udp_header = struct.pack('!HHHH', 
								self.srcport,
								self.destport,
								self.total_length,
								self.checksum)

		#Checksum optional in IPv4 for UDP
		#		
		#if self.checksum == 0:
		#	pseudo_header = struct.pack('!4s4sBBH',
		#								self.srcaddr,
		#								self.destaddr,
		#								0,
		#								socket.IPPROTOUDP,
		#								total_length)
		#	self.checksum = compute_checksum(pseudo_header+self.udp_header+self.data)
		#	self.assemble()

	@property
	def getdata(self):
		self.assemble()
		return self.udp_header + self.data
	
	def disassemble(recvdata):
		pass

class ICMPHeader:
	def __init__(self,icmptype,icmpcode,data,checksum=0):
		self.type = icmptype
		self.code = icmpcode
		self.data = data
		self.checksum = checksum
		
		logging.root.debug(self)

	def __repr__(self):
		return '<ICMPHeader: Type=%d, Code=%d>' % (self.code, self.type)

	def assemble(self):
		pass
	
	@classmethod
	def disassemble(cls,recvdata):
		log_str = 'ICMP Data Length=%d' % len(recvdata)
		logging.root.debug(log_str)

		icmptype, icmpcode, checksum = struct.unpack('!BBH', recvdata[0:4])
		
		if icmptype == 3 or icmptype == 11:
			data = recvdata[8:]
		else:
			data = struct.unpack('!4s', recvdata[4:8])
		
		return cls(icmptype, icmpcode, data, checksum)
