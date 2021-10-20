'''

    ###############################
    ##                           ##
    ##    one.com DDNS Script    ##
    ##                           ##
    ###############################
    | Author       | Lugico       |
    +--------------+--------------+
    | Email        | me@lugico.de |
    +--------------+--------------+
    | Discord      | Lugico#4592  |
    +--------------+--------------+
    | Version      | 2.1          |
    +--------------+--------------+
    | Last Updated | 2021-07-09   |
    +--------------+--------------+


    Note:
        This script is not very fail proof.
        something as little as a missing internet connection or a
        slight amount of packet loss can cause the script to crash
        or behave unexpectedly.

        I'm open to suggestions and will be glad to help if you
        have trouble getting the script to work.

'''



# YOUR ONE.COM LOGIN
USERNAME="email.address@example.com"
PASSWORD="Your Beautiful Password"

# YOUR DOMAIN ( NOT www.example.com, only example.com )"
DOMAIN="example.com"

# LIST OF SUBDOMAINS YOU WANT POINTING TO YOUR IP
SUBDOMAINS = ["myddns"]
# SUBDOMAINS = ["mutiple", "subdomains"]


# YOUR IP ADDRESS.
IP='AUTO'
# '127.0.0.1' -> IP  Address
# 'AUTO'      -> Automatically detect using ipify.org
# 'ARG'       -> Read from commandline argument ($ python3 ddns.py 127.0.0.1)


# CHECK IF IP ADDRESS HAS CHANGED SINCE LAST SCRIPT EXECUTION?
CHECK_IP_CHANGE = True
# True = only continue when IP has changed
# False = always continue

# PATH WHERE THE LAST IP SHOULD BE SAVED INBETWEEN SCRIPT EXECUTIONS
# not needed CHECK_IP_CHANGE is false
LAST_IP_FILE = "lastip.txt"


import requests
import json
import os
import sys

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
        f.write(IP);


def findBetween(haystack, needle1, needle2):
    index1 = haystack.find(needle1) + len(needle1)
    index2 = haystack.find(needle2, index1 + 1)
    return haystack[index1 : index2]


# will create a requests session and log you into your one.com account in that session
def loginSession(USERNAME,  PASSWORD, TARGET_DOMAIN=''):
    print("Logging in...")

    # create requests session
    session = requests.session();

    # get admin panel to be redirected to login page
    redirectmeurl = "https://www.one.com/admin/"
    r = session.get(redirectmeurl)

    # find url to post login credentials to from form action attribute
    substrstart = '<form id="kc-form-login" class="Login-form login autofill" onsubmit="login.disabled = true; return true;" action="'
    substrend = '"'
    posturl = findBetween(r.text, substrstart, substrend).replace('&amp;','&')

    # post login data
    logindata = {'username': USERNAME, 'password': PASSWORD, 'credentialId' : ''}
    session.post(posturl, data=logindata)

    print("Sent Login Data")

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
    #print(getres)
    return json.loads(getres)["result"]["data"];


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
    changeIP(s, findIdBySubdomain(records, subdomain), DOMAIN, subdomain, IP, 600)
