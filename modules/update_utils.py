# modules/update_utils.py
import sys
import modules.one_com_api as one_com_api
import logging

logger = logging.getLogger("one_com_ddns")

def _confirm_proceed(prompt: str) -> bool:
    """
    Prompt for confirmation unless running in a non-interactive shell.
    """
    if not sys.stdin.isatty():
        logger.info("Non-interactive shell detected; proceeding without user confirmation.")
        return True
    response = input(prompt)
    return response.strip().lower() == 'y'

def update_domain(s, domain, records, ip, ttl, current_dns_ip=None, skip_confirmation=False):
    """
    Updates the DNS record for a given domain, handling confirmation and logging.
    """
    record_obj = one_com_api.find_id_by_subdomain(records, domain)
    if record_obj is None:
        logger.error(f"Record '{domain}' could not be found.")
        return

    if current_dns_ip:
        logger.warning(f"Changing IP for {domain} from {current_dns_ip} to {ip} with TTL {ttl}.")
    else:
        logger.info(f"Changing IP for {domain} to {ip} with TTL {ttl}.")

    if skip_confirmation or _confirm_proceed("Do you want to proceed? (y/n): "):
        one_com_api.change_ip(s, record_obj, domain, ip, ttl)
    else:
        logger.info(f"Update for {domain} cancelled.")
