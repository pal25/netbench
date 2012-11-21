from udpprobe import UDPProbe
from dispatcher import EventLoop
import getopt, sys
import argparse

def parseargs():
	parser = argparse.ArgumentParser(description="NetBench: A tool to benchmark router hops and TTL")
	parser.add_argument("address", type=str, help="address to benchmark, defaults to localhost", default='127.0.0.1')
	parser.add_argument("--output", help="output file, defaults to stdout")
	parser.add_argument("--port", type=int, help="port number to probe, defaults to 50003", default=50003)
	
	args = parser.parse_args()

	if args.output:
		sys.stdout = open(args.output, 'w')

	run(args.address, args.port)

def run(addr, port):
	probe = UDPProbe(addr, port)

	loop = EventLoop()
	loop.add_dispatcher(probe)
	loop.run(timeout = 0.1)

if __name__ == '__main__':
	parseargs()
	
