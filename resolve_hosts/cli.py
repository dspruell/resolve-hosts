"""Command line interface."""

import argparse
import logging
import sys
from importlib.metadata import version

from aslookup.lookup import get_as_data
from dns.resolver import NXDOMAIN, LifetimeTimeout, NoAnswer, NoNameservers
from tabulate import tabulate

from .resolver import get_resolver
from .whois import get_domain_summary

try:
    from ujson import dumps as json_dumps
except ImportError:
    from json import dumps as json_dumps


__application_name__ = "resolve-hosts"
__version__ = version(__application_name__)

logging.basicConfig(
    level=logging.INFO, format="[%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


# Create a common parser to support shared arguments with different entry
# point parsers.
common_parser = argparse.ArgumentParser(add_help=False)
common_parser.add_argument(
    "-s",
    "--server",
    action="append",
    help="server (DNS resolver) to query (default: use system resolver)",
)
common_parser.add_argument(
    "-d", "--debug", action="store_true", help="enable debug output"
)
common_parser.add_argument(
    "-V",
    "--version",
    action="version",
    version=__version__,
    help="print package version",
)


def resolve_hosts():
    """Run host resolution CLI."""
    epilog = (
        "Additional resolvers may be specified by passing multiple "
        "--server options."
    )
    parser = argparse.ArgumentParser(
        description="Resolve list of DNS hostnames.",
        epilog=epilog,
        parents=[common_parser],
    )
    parser.add_argument(
        "infile",
        type=argparse.FileType("r"),
        default=sys.stdin,
        nargs="?",
        help="source for list of names to resolve (default: standard input)",
    )
    parser.add_argument(
        "-j", "--json", action="store_true", help="output JSON data"
    )
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.debug(
        "configured to use resolver(s): %s",
        args.server if args.server else "local system",
    )

    resp_data = []

    resolver = get_resolver(args.server)

    # Resolve input names
    for fqdn in args.infile:
        # Clear up any leading/trailing whitespace, and gracefully ignore
        # comments or blank lines.
        fqdn = fqdn.strip()
        if (fqdn == "") or fqdn.startswith("#"):
            logger.debug("skipping input: >>%s<<", fqdn)
            continue
        try:
            answer = resolver.resolve(fqdn)
        except NXDOMAIN:
            answer = ["NXDOMAIN"]
        except NoAnswer:
            answer = ["NODATA (no answer)"]
        if args.json:
            resp_data.append({fqdn: [str(addr) for addr in answer]})
        else:
            resp_data.append((fqdn, " ".join([str(addr) for addr in answer])))

    if args.json:
        print(json_dumps({"data": resp_data}, indent=4))
    else:
        print(tabulate(resp_data, tablefmt="plain"))


def probe_domain():
    """Run domain discovery CLI."""
    parser = argparse.ArgumentParser(
        description="Return basic information about a domain.",
        parents=[common_parser],
    )
    parser.add_argument(
        "domain", help="domain for which to return information"
    )
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    resolver = get_resolver(args.server)

    domain = args.domain.strip()

    resp_data = {}

    domain_reg = get_domain_summary(domain)
    if domain_reg:
        resp_data.update({"WHOIS": domain_reg})

    # Process desired record types by converting to string blobs and adding to
    # output.
    for rdtype in ("SOA", "NS", "MX", "TXT"):
        try:
            answer = resolver.resolve(domain, rdtype, search=False)
            resp_data.update({rdtype: str(answer.rrset)})
        except NXDOMAIN:
            logger.warning(
                "%s (%s record) returned %s", domain, rdtype, "NXDOMAIN"
            )
        except NoAnswer:
            logger.warning(
                "%s (%s record) returned %s",
                domain,
                rdtype,
                "NODATA (no answer)",
            )
        except LifetimeTimeout as e:
            parser.error(f"failed to resolve domain: {e}")
        except NoNameservers as e:
            logger.warning(
                "%s (%s record) returned error: %s", domain, rdtype, e
            )

    # Process A records by converting to string blobs and adding to output.
    # Additionally perform ASN lookups and add to output.
    try:
        answer = resolver.resolve(domain, "A", search=False)
        resp_data.update({"A": str(answer.rrset)})
        resp_data["ASN"] = []
        for ans in answer:
            addr = ans.to_text()
            asdata = get_as_data(addr, "cymru")
            resp_data["ASN"].append(asdata.as_text())
    except NXDOMAIN:
        logger.warning("%s (A record) returned %s", domain, "NXDOMAIN")
    except NoAnswer:
        logger.warning(
            "%s (A record) returned %s", domain, "NODATA (no answer)"
        )

    output_data = {}
    for d in ["WHOIS", "SOA", "NS", "MX", "TXT", "A"]:
        if resp_data.get(d):
            output_data.update({d: resp_data.get(d)})

    logger.debug("resp_data: %s", resp_data)

    if resp_data.get("ASN"):
        output_data.update({"ASN": "\n".join(resp_data["ASN"])})

    print("\n\n".join([v for k, v in output_data.items()]))
