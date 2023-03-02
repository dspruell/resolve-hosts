"Resolve list of DNS hostnames."

import argparse
from ipaddress import ip_address
import logging
import sys

from dns.resolver import Resolver, resolve, NXDOMAIN
from tabulate import tabulate

try:
    from ujson import dumps as json_dumps
except ImportError:
    from json import dumps as json_dumps


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
    epilog = (
        "Additional resolvers may be specified by passing multiple "
        "--server options."
    )
    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    parser.add_argument(
        "infile",
        type=argparse.FileType("r"),
        default=sys.stdin,
        nargs="?",
        help="source for list of names to resolve (default: standard input)",
    )
    parser.add_argument(
        "-s",
        "--server",
        action="append",
        help="server (DNS resolver) to query (default: use system resolver)",
    )
    parser.add_argument(
        "-j", "--json", action="store_true", help="output JSON data"
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

    res_addrs = []

    # if args.server is not an IP, resolve it first
    if args.server:
        res_addrs = resolve_servers(args.server)
        logging.debug(
            "effective resolver address(es): %s",
            res_addrs,
        )

    resp_data = []
    resolver = Resolver()
    if res_addrs:
        resolver.nameservers = res_addrs

    # Resolve input names
    for fqdn in args.infile:
        # Clear up any leading/trailing whitespace, and gracefully ignore
        # comments or blank lines.
        fqdn = fqdn.strip()
        if (fqdn == "") or fqdn.startswith("#"):
            logging.debug("skipping input: >>%s<<", fqdn)
            continue
        try:
            answer = resolver.resolve(fqdn)
        except NXDOMAIN:
            answer = ["NXDOMAIN"]
        if args.json:
            resp_data.append({fqdn: [str(addr) for addr in answer]})
        else:
            resp_data.append((fqdn, " ".join([str(addr) for addr in answer])))

    if args.json:
        print(json_dumps({"data": resp_data}, indent=4))
    else:
        print(tabulate(resp_data, tablefmt="plain"))
