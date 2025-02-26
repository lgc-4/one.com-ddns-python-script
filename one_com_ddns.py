'''
    #################################
    ##                               ##
    ##    one.com DDNS Script        ##
    ##                               ##
    #################################
    | Version       | 2.4             |
    +--------------+----------------+
    | Last Updated | 2023-10-05       |
    +--------------+----------------+

    +----------------+-------------------------+
    | Initial Author | Lugico <main@lugico.de> |
    +----------------+-------------------------+
    | Contributors   | Vigge                   |
    +----------------+-------------------------+


    Note:
        This script is not very fail proof.
        Very few possible exceptions are handled, something as simple
        as a missing internet connection will make the script behave
        unexpectedly. Use with caution.

        If you have any problems or suggestions, please open an issue
        on github or send me an email (main@lugico.de)
'''

import modules.dns_utils as dns_utils
import modules.one_com_config as config
import modules.one_com_api as one_com_api
import modules.logger as logger_module
import modules.update_utils as update_utils

logger = logger_module.setup_logging()  # Setup logging

# #################################
# ##                            ##
# ##    HARDCODED VALUES        ##
# ##                            ##
# #################################
# If you wish to hardcode values below and disable cli/env parsing set validate_required=False
settings = config.parse_config(validate_required=True)

# ONE.COM LOGIN
USERNAME = settings.username
PASSWORD = settings.password

# YOUR DOMAIN (NOT www.example.com, www2.example.com)
DOMAINS = settings.domains

# YOUR IP ADDRESS. DEFAULTS TO RESOLVING VIA ipify.org, set to 'ARG' to take from script argument
IP = settings.ip

# FORCE UPDATE DNS RECORD
FORCE_UPDATE = settings.force_update

# TTL VALUE FOR DNS RECORD
TTL = settings.ttl

# SKIP CONFIRMATION
SKIP_CONFIRMATION = settings.skip_confirmation

# Create login session - Session is created only once outside the domain loop
s = one_com_api.login_session(USERNAME, PASSWORD)

# loop through list of domains
for DOMAIN in DOMAINS:
    print()
    logger.info(f"Processing domain: {DOMAIN}")
    one_com_api.select_admin_domain(s, DOMAIN)
    records = one_com_api.get_custom_records(s, DOMAIN)

    logger.info(f"Attempting to get current DNS IP for: {DOMAIN}")
    current_dns_ip_info = dns_utils.get_ip_and_ttl(DOMAIN)

    if current_dns_ip_info:
        current_dns_ip, current_ttl = current_dns_ip_info
        logger.info(f"Current DNS IP for {DOMAIN}: {current_dns_ip}, TTL: {current_ttl}")

        if not FORCE_UPDATE and current_dns_ip == IP:
            logger.info(f"IP Address hasn't changed for {DOMAIN}. Aborting update for this domain.")
            continue

        update_utils.update_domain(s, DOMAIN, records, IP, TTL, current_dns_ip, SKIP_CONFIRMATION)
    else:
        logger.warning(f"Could not retrieve current DNS IP for {DOMAIN} after multiple retries. Proceeding with update anyway.")
        update_utils.update_domain(s, DOMAIN, records, IP, TTL, None, SKIP_CONFIRMATION)

logger.info("DDNS update process completed.")