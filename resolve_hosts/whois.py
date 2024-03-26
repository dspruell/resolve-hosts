"""WHOIS lookup routines."""

import logging

from tabulate import tabulate
from whois_format import get_domain_whois


logger = logging.getLogger(__name__)


def get_domain_summary(domain):
    """Return summary domain information.

    Query WHOIS for information on given domain and return in conpact form.
    """
    resp_data = get_domain_whois([domain])
    logger.debug("resp_data: %s", resp_data)
    if resp_data["warnings"]:
        logger.warning(
            "error in domain lookup: %s",
            "\n".join([f"{d}: {m}" for d, m in resp_data["warnings"]]),
        )
    return tabulate(resp_data["responses"], tablefmt="plain")
