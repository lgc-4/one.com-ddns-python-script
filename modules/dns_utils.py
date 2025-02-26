# modules/dns_utils.py
import dns.resolver
import dns.exception
import logging

logger = logging.getLogger("one_com_ddns")

def get_authoritative_ns(domain):
    """
    Recursively finds the authoritative nameservers for a given domain.
    Tries parent domains if no NS records are found or in case of timeout or other DNS errors
    (except for NXDOMAIN, where it stops and indicates domain does not exist).

    Args:
        domain (str): The domain to query.

    Returns:
        list: A list of authoritative nameserver hostnames, or None if not found or domain does not exist.
    """
    try:
        answers = dns.resolver.resolve(domain, 'NS')
        return [data.to_text() for data in answers]
    except dns.resolver.NoAnswer:
        exception_type = "NoAnswer"
    except dns.exception.Timeout:
        exception_type = "Timeout"
    except dns.resolver.NXDOMAIN:
        exception_type = "NXDOMAIN"
    except dns.exception.DNSException as e:
        exception_type = f"DNSException: {e}"

    # Handle exceptions that might indicate trying parent domain
    if exception_type in ["NoAnswer", "Timeout", "DNSException", "NXDOMAIN"]:
        parts = domain.split('.')
        if len(parts) > 2:  # Check if there's a parent domain
            parent_domain = '.'.join(parts[1:])
            return get_authoritative_ns(parent_domain)
        else:
            logger.warning(f"No authoritative NS for {domain} and no parent domain to try after exception: {exception_type}")
            return None  # No parent domain, give up
    else: # Should not reach here, but as a fallback. For completeness.
        logger.error(f"Failed to get NS for {domain} due to: {exception_type}")
        return None

def get_ip_and_ttl(domain, ns_servers=None):
    """
    Gets the IP address and TTL of a domain from the authoritative nameservers.

    Args:
        domain (str): The domain to query.
        optional ns_servers (list): A list of authoritative nameserver hostnames.

    Returns:
        tuple: A tuple containing the IP address and TTL, or None if not found.
    """
    if ns_servers is None:
        ns_servers = get_authoritative_ns(domain)
        if ns_servers is None:
            return None
    resolver = dns.resolver.Resolver()
    tmp = [dns.resolver.resolve(ns, 'A')[0].address for ns in ns_servers]
    resolver.nameservers = tmp
    try:
        answers = resolver.resolve(domain, 'A')
        for rdata in answers:
            return rdata.address, answers.ttl
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout, dns.exception.DNSException) as e:
        logger.warning(f"Error getting IP and TTL for {domain}: {e}")
        return None