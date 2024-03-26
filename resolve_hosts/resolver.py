"""Resolver routines."""

import logging
from ipaddress import ip_address

from dns.resolver import Resolver, resolve


logger = logging.getLogger(__name__)


def resolve_servers(servers: list) -> list:
    """
    Resolve specified resolvers.

    Return IP addresses of input DNS servers, after resolving any
    hostnames.

    """
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


def get_resolver(servers: list = []) -> Resolver:
    """
    Create a name resolver and return it to the caller.

    Return a configured resolver to the caller. If nameservers are supplied as
    input, resolve any names to IP addresses and set them as resolver hosts on
    the resolver prior to returning.

    """
    res_addrs = []

    # if args.server is not an IP, resolve it first
    if servers:
        res_addrs = resolve_servers(servers)
        logger.debug(
            "effective resolver address(es): %s",
            res_addrs,
        )

    resolver = Resolver()
    if res_addrs:
        resolver.nameservers = res_addrs

    return resolver
