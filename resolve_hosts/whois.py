"""WHOIS lookup routines."""

import logging

from tabulate import tabulate
from whois_format import get_domain_whois


def get_domain_summary(domain):
    """Return summary domain information.

    Query WHOIS for information on given domain and return in conpact form.
    """
    resp_data = get_domain_whois([domain])
    if resp_data["warnings"]:
        logging.warning(
            "error in domain lookup: %s", "\n".join(resp_data["warnings"])
        )
    return tabulate(resp_data["responses"], tablefmt="plain")
