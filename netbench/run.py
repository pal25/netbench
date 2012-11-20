from udpprobe import UDPProbe
from dispatcher import EventLoop

def main(addr=''):
	port = 50003
	probe = UDPProbe(addr, port)

	loop = EventLoop()
	loop.add_dispatcher(probe)
	loop.run(timeout = 0.1)

if __name__ == '__main__':
	main(addr = 'google.com')
	
