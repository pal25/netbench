from udpprobe import UDPProbe
from icmphandler import ICMPHandler
from eventloop import EventLoop
import argparse, sys
import logging
import logging.config

def parseargs():
	parser = argparse.ArgumentParser(description="NetBench: A tool to benchmark router hops and TTL")
	parser.add_argument("--level", type=str, help="logging level to record, defaults to error", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
	parser.add_argument("address", nargs='+', type=str, help="address to benchmark, defaults to localhost", default="127.0.0.1")
	parser.add_argument("--output", type=str, help="output file, defaults to stdout")
	parser.add_argument("--port", type=int, help="port number to probe, defaults to 50003", default=50003)
	parser.add_argument("--timeout", type=float, help="timeout for pooling the udpprobe, defaults to 0.1sec", default=0.1)
	
	args = parser.parse_args()

	output = None
	if args.output:
		output = open(args.output, 'a')

	if args.level == 'DEBUG':
		level = logging.DEBUG
	elif args.level == 'INFO':
		level = logging.INFO
	elif args.level == 'WARNING':
		level = logging.WARNING
	elif args.level == 'ERROR':
		level = logging.ERROR
	elif args.level == 'CRITICAL':
		level = logging.CRITICAL
	else:
		level = logging.ERROR
	logging.config.fileConfig('logging.conf')
	logging.root.setLevel(level)

	destaddrs = []
	for destaddr in args.address:
		destaddrs.append((destaddr, args.port))
		
	run(destaddrs, args.timeout, output)

def run(destaddrs, timeout, output):
	eventloop = EventLoop()
	
	for destaddr in destaddrs:
		eventloop.add_dispatcher(UDPProbe(destaddr, output))
		eventloop.add_dispatcher(ICMPHandler(destaddr))
			
	eventloop.run(timeout)

if __name__ == '__main__':
	parseargs()
	
