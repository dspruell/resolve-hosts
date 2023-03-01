"Resolve list of DNS hostnames."

import argparse
from ipaddress import ip_address
from json import dumps as json_dumps
import logging

from dns import query
from dns.resolver import Resolver, resolve, NXDOMAIN
from tabulate import tabulate


logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def resolve_servers(servers: list) -> list:
    "Return IP addresses of input DNS servers, after resolving any hostnames."

    results = []
    for s in servers:
        try:
            ip_address(s)
            results.append(s)
        except ValueError:
            r = resolve(s)
            for addr in r:
                results.append(str(addr))
    return results


def cli():
    description = "Resolve list of DNS hostnames."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "infile",
        type=argparse.FileType("r"),
        help=("source input for list of names to resolve (default: standard input)"),
    )
    parser.add_argument(
        "-s",
        "--server",
        action="append",
        help="server (DNS resolver) to query (default: use system resolver)",
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="enable debug output"
    )
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logging.debug(
        "configured to use resolver(s): %s",
        args.server if args.server else "local system",
    )

    resolver_kwargs = {"resolvers": []}

    # if args.server is not an IP, resolve it first
    if args.server:
        resolver_kwargs["resolvers"] = resolve_servers(args.server)
        logging.debug(
            "effective resolver address(es): %s",
            resolver_kwargs["resolvers"],
        )

    resp_data = []
    resolver = Resolver()
    if resolver_kwargs["resolvers"]:
        resolver.nameservers = resolver_kwargs["resolvers"]

    for fqdn in args.infile:
        fqdn = fqdn.strip()
        try:
            answer = resolver.resolve(fqdn)
        except NXDOMAIN:
            answer = ["NXDOMAIN"]
        resp_data.append((fqdn, " ".join([str(addr) for addr in answer])))

    print(tabulate(resp_data, tablefmt="plain"))
