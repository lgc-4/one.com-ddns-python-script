'''

    #################################
    ##                             ##
    ##     one.com DDNS Script     ##
    ##                             ##
    #################################
    | Version      | 2.3            |
    +--------------+----------------+
    | Last Updated | 2022-04-02     |
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
import os
import requests
import json
import sys

# YOUR ONE.COM LOGIN
#USERNAME="email.address@example.com"
USERNAME = os.getenv('Username')
#PASSWORD="Your Beautiful Password"
PASSWORD = os.getenv('Password')
# YOUR DOMAIN ( NOT www.example.com, only example.com )"
#DOMAIN="example.com"
DOMAIN = os.getenv('Domain')
# LIST OF SUBDOMAINS YOU WANT POINTING TO YOUR IP
#SUBDOMAINS = ["myddns"]
# SUBDOMAINS = ["mutiple", "subdomains"]
SUBDOMAINS = os.getenv('SubDomains').split(',')

# YOUR IP ADDRESS.
#IP='AUTO'
IP = os.getenv('IP','AUTO')
# '127.0.0.1' -> IP  Address
# 'AUTO'      -> Automatically detect using ipify.org
# 'ARG'       -> Read from commandline argument ($ python3 ddns.py 127.0.0.1)


# CHECK IF IP ADDRESS HAS CHANGED SINCE LAST SCRIPT EXECUTION?
#CHECK_IP_CHANGE = True
CHECK_IP_CHANGE = os.getenv('Change','true').lower() == 'true'
# True = only continue when IP has changed
# False = always continue

# PATH WHERE THE LAST IP SHOULD BE SAVED INBETWEEN SCRIPT EXECUTIONS
# not needed CHECK_IP_CHANGE is false
LAST_IP_FILE = "lastip.txt"

print(f"Running with options USERNAME: {USERNAME}, DOMAIN:{DOMAIN} SUBDomains: {SUBDOMAINS} IPMode: {IP}, Change detection: {CHECK_IP_CHANGE}")

if IP == 'AUTO':
    IP = requests.get("https://api.ipify.org/").text
    print(f"Detected IP: {IP}")
elif IP == 'ARG':
    if (len(sys.argv) < 2):
        raise Exception('No IP Adress provided in commandline parameters')
        exit()
    else:
        IP = sys.argv[1]

if CHECK_IP_CHANGE:
    try:
        # try to read file
        with open(LAST_IP_FILE,"r") as f:
            if (IP == f.read()):
                # abort if ip in file is same as current
                print("IP Address hasn't changed. Aborting")
                exit()
    except IOError:
        pass

    # write current ip to file
    with open(LAST_IP_FILE,"w") as f:
        f.write(IP)


def findBetween(haystack, needle1, needle2):
    index1 = haystack.find(needle1) + len(needle1)
    index2 = haystack.find(needle2, index1 + 1)
    return haystack[index1 : index2]


# will create a requests session and log you into your one.com account in that session
def loginSession(USERNAME,  PASSWORD, TARGET_DOMAIN=''):
    print("Logging in...")

    # create requests session
    session = requests.session()

    # get admin panel to be redirected to login page
    redirectmeurl = "https://www.one.com/admin/"
    r = session.get(redirectmeurl)

    # find url to post login credentials to from form action attribute
    substrstart = '<form id="kc-form-login" class="Login-form login autofill" onsubmit="login.disabled = true; return true;" action="'
    substrend = '"'
    posturl = findBetween(r.text, substrstart, substrend).replace('&amp;','&')

    # post login data
    logindata = {'username': USERNAME, 'password': PASSWORD, 'credentialId' : ''}
    response = session.post(posturl, data=logindata)
    if response.text.find("Invalid username or password.") != -1:
        print("!!! - Invalid credentials. Exiting")
        exit(1)

    print("Login successful.")

    # For accounts with multiple domains it seems to still be needed to select which target domain to operate on.
    if TARGET_DOMAIN:
        print("Setting active domain to: {}".format(TARGET_DOMAIN))
        selectAdminDomain(session, TARGET_DOMAIN)

    return session


def selectAdminDomain(session, DOMAIN):
    request_str = "https://www.one.com/admin/select-admin-domain.do?domain={}".format(DOMAIN)
    session.get(request_str)


# gets all DNS records on your domain.
def getCustomRecords(session, DOMAIN):
    print("Getting Records")
    getres = session.get("https://www.one.com/admin/api/domains/" + DOMAIN + "/dns/custom_records").text
    if len(getres) == 0:
        print("!!! - No records found. Exiting")
        exit()
    return json.loads(getres)["result"]["data"]


# finds the record id of a record from it's subdomain
def findIdBySubdomain(records, subdomain):
    print("searching domain '" + subdomain + "'")
    for obj in records:
        if obj["attributes"]["prefix"] == subdomain:
            print("Found Domain '" + subdomain + "': " + obj["id"])
            return obj["id"]
    return ""


# changes the IP Address of a TYPE A record. Default TTL=3800
def changeIP(session, ID, DOMAIN, SUBDOMAIN, IP, TTL=3600):
    print("Changing IP on subdomain '" + SUBDOMAIN + "' - ID '" + ID + "' TO NEW IP '" + IP + "'")

    tosend = {"type":"dns_service_records","id":ID,"attributes":{"type":"A","prefix":SUBDOMAIN,"content":IP,"ttl":TTL}}

    dnsurl="https://www.one.com/admin/api/domains/" + DOMAIN + "/dns/custom_records/" + ID

    sendheaders={'Content-Type': 'application/json'}

    session.patch(dnsurl, data=json.dumps(tosend), headers=sendheaders)

    print("Sent Change IP Request")



# Create login session
s = loginSession(USERNAME, PASSWORD, DOMAIN)

# get dns records
records = getCustomRecords(s, DOMAIN)
#print(records)

# loop through list of subdomains
for subdomain in SUBDOMAINS:
    #change ip address
    recordid = findIdBySubdomain(records, subdomain)
    if recordid == "":
        print("!!! - Record '" + subdomain + "' could not be found.")
        continue
    changeIP(s, recordid, DOMAIN, subdomain, IP, 600)