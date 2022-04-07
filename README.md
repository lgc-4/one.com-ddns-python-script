# one.com DDNS Script

The name is pretty self explanatory. It's a Python script for updating type A DNS records at one.com.

## Required Packages
- `requests`
- `json`
- `sys`

## Usage
At the very top of the Script there are some customization options and variables for your one.com control panel login credentials.

### Login Credentials
These are the credentials you use to log into your control panel.
```python
# YOUR ONE.COM LOGIN
USERNAME="email.address@example.com"
PASSWORD="Your Beautiful Password"
```

### Domain
Since you can have multiple domains on one account you need to specify which domain's DNS records you want to edit.
```python
# YOUR DOMAIN ( NOT www.example.com, only example.com )"
DOMAIN="example.com"
```

### Subdomains
Next up is a list with all the subdomains you want to point at your chosen IP address.
```python
# LIST OF SUBDOMAINS YOU WANT POINTING TO YOUR IP
SUBDOMAINS = ["myddns"]
```
To have the domain itself point to your chosen IP address, instead of a subdomain, insert an empty string into the array.
```python
SUBDOMAINS = ["myddns",""]
# myddns.example.com AND example.com will point to the chosen IP address
```

Note that the script is not capable of creating new DNS records.

It can only edit existing ones.

### IP Address
The `IP` option allows you to specify the IP Address you want your DNS records pointing to.

You can
- directly specify an IP Address in the script (`'127.0.0.1'`, `'1.1.1.1'`, ...)
- have the script automatically detect your public IP Address through [ipify](https://www.ipify.org) (`'AUTO'`)
- define an IP Address using command-line arguments (`'ARG'`, execute like `python3 one_com_ddns.py 127.0.0.1`)
```python
IP='127.0.0.1'
IP='AUTO'
IP='ARG'
```

### IP Change Detection
The `CHECK_IP_CHANGE` option allows you to abort the script, if your IP Address hasn't changed since it was last executed.

In order to detect an IP Address change, your last IP Address has to be saved in a file, specified in `LAST_IP_FILE`. If your given/detected IP Address differs from the one in the file, the script will continue
```python
# CHECK IF IP ADDRESS HAS CHANGED SINCE LAST SCRIPT EXECUTION?
CHECK_IP_CHANGE = True
# True = only continue when IP has changed
# False = always continue

# PATH WHERE THE LAST IP SHOULD BE SAVED INBETWEEN SCRIPT EXECUTIONS
# not needed CHECK_IP_CHANGE is false
LAST_IP_FILE = "lastip.txt"
```

## Docker

To build docker from dockerfile: Replace imagenamexyz with your own
```
docker build --rm -f "dockerfile" -t imagenameXYZ:tag . 
```
Dockercompose example:
```
version: '3.3'
services:
   one:
     image: imagenameXYZ:latest
     environment:
      - Username=example@domain.com
      - Password=pwd
      - Domain=domain.com
      - SubDomains=sub
```


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Any feature requests are welcome as well.

## Need Help?
Don't hesitate to contact me:
- [main@lugico.de](mailto:main@lugico.de)
