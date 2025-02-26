# modules/one_com_api.py
import requests
import json
import tldextract
import logging

logger = logging.getLogger("one_com_ddns")

def _find_between(haystack, needle1, needle2):
    index1 = haystack.find(needle1) + len(needle1)
    index2 = haystack.find(needle2, index1 + 1)
    return haystack[index1 : index2]

def login_session(username, password):
    logger.info("Logging in...")
    session = requests.session()
    redirect_url = "https://www.one.com/admin/"
    try:
        r = session.get(redirect_url)
    except requests.ConnectionError:
        logger.error("Connection to one.com failed.")
        raise SystemExit("Connection to one.com failed.")

    post_url = _find_between(r.text, '<form id="kc-form-login" class="Login-form login autofill" onsubmit="login.disabled = true; return true;" action="', '"').replace('&amp;', '&')
    login_data = {'username': username, 'password': password, 'credentialId': ''}
    response = session.post(post_url, data=login_data)
    if "Invalid username or password." in response.text:
        logger.error("Invalid credentials. Exiting")
        exit(1)
    logger.info("Login successful.")
    return session

def select_admin_domain(session, domain):
    request_str = f"https://www.one.com/admin/select-admin-domain.do?domain={domain}"
    session.get(request_str)

def get_custom_records(session, domain):
    extracted = tldextract.extract(domain)
    primary_domain = f"{extracted.domain}.{extracted.suffix}"
    logger.info(f"Getting Records for primary domain: {primary_domain} (Requesting for: {domain})")
    dns_url = f"https://www.one.com/admin/api/domains/{primary_domain}/dns/custom_records"
    try:
        response = session.get(dns_url)
        response.raise_for_status()
        get_res = response.text
        if not get_res:
            raise ValueError("Empty response from API")
        return json.loads(get_res)["result"]["data"]
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching DNS records for domain: {domain}. HTTP Status Code: {e.response.status_code if e.response else 'N/A'}")
        raise SystemExit(f"Failed to get DNS records for domain {domain}: {e}") from e
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.error(f"Error parsing JSON response for domain: {domain}. Response text was: {get_res}")
        raise SystemExit(f"Failed to parse DNS records JSON for domain {domain}: {e}") from e

def find_id_by_subdomain(records, subdomain):
    extracted_subdomain = tldextract.extract(subdomain).subdomain
    logger.info(f"searching domain prefix for: '{extracted_subdomain}'")
    for obj in records:
        if obj["attributes"]["prefix"] == extracted_subdomain:
            logger.info(f"Found Domain Prefix '{extracted_subdomain}': {obj['id']}")
            return obj
    return None

def change_ip(session, record, domain, ip, ttl):
    record_id = record["id"]
    current_ttl = record["attributes"]["ttl"]
    actual_ttl = ttl if ttl is not None else current_ttl
    extracted = tldextract.extract(domain)
    primary_domain = f"{extracted.domain}.{extracted.suffix}"
    subdomain = extracted.subdomain
    logger.info(f"Changing IP on record for subdomain '{subdomain}' - ID '{record_id}' TO NEW IP '{ip}' with TTL '{actual_ttl}' on primary domain '{primary_domain}'")
    to_send = {
        "type": "dns_service_records",
        "id": record_id,
        "attributes": {
            "type": "A",
            "prefix": subdomain,
            "content": ip,
            "ttl": actual_ttl
        }
    }
    dns_url = f"https://www.one.com/admin/api/domains/{primary_domain}/dns/custom_records/{record_id}"
    send_headers = {'Content-Type': 'application/json'}
    try:
        response = session.patch(dns_url, data=json.dumps(to_send), headers=send_headers)
        response.raise_for_status()
        logger.info("Sent Change IP Request")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error updating IP for record with subdomain '{subdomain}': {e}")
        status_code = e.response.status_code if e.response else 'N/A'
        logger.error(f"HTTP Status Code: {status_code}")
        raise SystemExit(f"Failed to update IP for record with subdomain {subdomain}: {e}") from e