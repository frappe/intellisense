import argparse
import logging

from .server import frappe_server

logging.basicConfig(filename="frappe-ls.log", level=logging.DEBUG, filemode="w")


def add_arguments(parser):
	parser.description = "Frappe Language Server"

	parser.add_argument(
		"--tcp", action="store_true", help="Use TCP server instead of stdio"
	)
	parser.add_argument("--host", default="127.0.0.1", help="Bind to this address")
	parser.add_argument("--port", type=int, default=2087, help="Bind to this port")


def main():
	parser = argparse.ArgumentParser()
	add_arguments(parser)
	args = parser.parse_args()

	if args.tcp:
		print(f"starting server at {args.port}")
		frappe_server.start_tcp(args.host, args.port)
	else:
		frappe_server.start_io()


if __name__ == "__main__":
	main()
