from udpprobe import UDPProbe
from icmphandler import ICMPHandler
from dispatcher import EventLoop
import argparse, sys
import logging
import logging.config

def parseargs():
	parser = argparse.ArgumentParser(description="NetBench: A tool to benchmark router hops and TTL")
	parser.add_argument("--level", type=str, help="logging level to record, defaults to error", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
	parser.add_argument("address", type=str, help="address to benchmark, defaults to localhost", default="127.0.0.1")
	parser.add_argument("--output", type=str, help="output file, defaults to stdout")
	parser.add_argument("--port", type=int, help="port number to probe, defaults to 50003", default=50003)
	parser.add_argument("--timeout", type=float, help="timeout for pooling the udpprobe, defaults to 0.1sec", default=0.1)
	
	args = parser.parse_args()

	if args.output:
		sys.stdout = open(args.output, 'w')

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

	run((args.address, args.port), args.timeout)

def run(destaddr, timeout):
	loop = EventLoop()

	probe = UDPProbe(destaddr, loop.stop)
	handler = ICMPHandler(destaddr, probe.binary_search)
	
	loop.add_dispatcher(probe)
	loop.add_dispatcher(handler)
	loop.run(timeout)

if __name__ == '__main__':
	parseargs()
	
