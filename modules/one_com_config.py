# modules/one_com_config.py
import os
import argparse
import requests
import logging

logger = logging.getLogger("one_com_ddns")

def parse_config(validate_required=True):
    """
    Parses configuration for the one.com DDNS script from command-line arguments,
    environment variables, and returns None as default if no value is set.

    Configuration is prioritized: command-line arguments > environment variables > None (if unset).

    Key configuration parameters:
        - username (-u, --username): one.com username (defaults to None if unset)
        - password (-p, --password): one.com password (defaults to None if unset)
        - domains (-d, --domains): List of domain names (e.g.,-d example.com example2.com) (defaults to None if unset)
        - ip (-i, --ip): IP address source ('AUTO', 'ARG', or IP) (defaults to None if unset)
        - force-update (-f, --force-update): Force DNS update (defaults to None if unset)
        - ttl (-t, --ttl): TTL for DNS records (defaults to None if unset)
        - skip-confirmation (--skip-confirmation): Skip confirmation prompts (defaults to False if unset)

    Returns:
        argparse.Namespace: Object containing configuration parameters.

    Raises:
        ValueError: If validate_required is True and username, password, or domain are None
                    after parsing.
        SystemExit: If automatic IP retrieval fails when 'AUTO' is selected
                    or if no IP address is provided as a command-line argument
                    when 'ARG' is selected.
    """
    parser = argparse.ArgumentParser(description="one.com DDNS Script Configuration")

    parser.add_argument("-u", "--username", help="one.com username", default=os.environ.get("USERNAME"))
    parser.add_argument("-p", "--password", help="one.com password", default=os.environ.get("PASSWORD"))
    env_domains = os.environ.get("DOMAINS")
    if env_domains is not None:
        env_domains = env_domains.split(',')

    parser.add_argument("-d", "--domains", nargs="+", help="List of domain names (e.g.,-d example.com example2.com)", default=env_domains)
    parser.add_argument("-i", "--ip", help="IP address ('AUTO', or IP)", default=os.environ.get("IP", "AUTO"))

    env_force = os.environ.get("FORCE_DNS_UPDATE")
    if env_force is not None:
        env_force = env_force.lower()

    parser.add_argument("-f", "--force-update", action="store_true", help="Force DNS update (skip IP check)", default=env_force)
    parser.add_argument("-t", "--ttl", type=int, help="TTL value for DNS records", default=os.environ.get("TTL"))
    parser.add_argument("-y", "--skip-confirmation", action="store_true", help="Skip confirmation prompts", default=os.environ.get("SKIP_CONFIRMATION"))

    args = parser.parse_args()

    # Basic validation (ONLY IF validate_required is True)
    if validate_required:
        if not args.username:
            raise ValueError("Username is required (command-line or USERNAME env var)")
        if not args.password:
            raise ValueError("Password is required (command-line or PASSWORD env var)")
        if not args.domains:
            raise ValueError("Domain is required (command-line or DOMAIN env var)")

    # Handle IP address retrieval
    if args.ip == "AUTO":
        try:
            args.ip = requests.get("https://api.ipify.org/").text
        except requests.ConnectionError:
            logger.error("Failed to get IP Address from ipify")
            raise SystemExit("Failed to get IP Address from ipify")
        logger.info(f"Detected external IP: {args.ip}")

    return args