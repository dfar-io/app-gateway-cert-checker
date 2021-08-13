"""Cycles through all SSL certs of Azure Application Gateways
   and reports any in range of expiration."""

import subprocess
import os
import json
import datetime
import sys
from dotenv import load_dotenv

def get_env_vars():
    '''Validates and returns environment variables.'''
    env_dict = {
        'client_id': os.getenv('CLIENT_ID'),
        'client_secret': os.getenv('CLIENT_SECRET'),
        'tenant_id': os.getenv('TENANT_ID')
    }

    for value in env_dict.items():
        if value is None:
            raise OSError(f'{property} environment variable not set.')

    return env_dict

env = get_env_vars()

def verify_az():
    '''Verifies az is set up.'''
    subprocess.run(["az", "--version"],
                    check=True,
                    stdout=subprocess.DEVNULL)

def login_to_az():
    '''Logs into az using service principal provided in env. variables'''
    subprocess.run(["az", "login", "--service-principal",
        "-u", env['client_id'],
        "-p", env['client_secret'],
        "--tenant", env['tenant_id']],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)

def get_app_gateways():
    '''Gets all app gateways'''
    result = subprocess.run(["az", "network", "application-gateway", "list"],
                             check=True,
                             capture_output=True)
    return json.loads(result.stdout)

def get_ssl_expiration(host):
    '''Gets the SSL cert expiration date of a host.'''
    with subprocess.Popen(("openssl", "s_client",
            "-connect", f'{host}:443', "-servername", host),
            stdout=subprocess.PIPE) as popen:
        end_date_string = subprocess.check_output(('openssl', 'x509',
            '-noout', '-enddate'), stdin=popen.stdout)

    # manipulate the end date string given into a datetime object
    end_date_string = str(end_date_string).split("=")[1].split()
    month_abbv = end_date_string[0]
    day = int(end_date_string[1])
    year = int(end_date_string[3])
    month_date_object = datetime.datetime.strptime(month_abbv, "%b")
    month = month_date_object.month

    return datetime.date(year, month, day)

def get_hosts_requiring_renewal(app_gateways):
    ''' Given App Gateways, get the hosts that require renewal.'''
    result = []
    for app_gateway in app_gateways:
        http_listeners = app_gateway['httpListeners']

        for http_listener in http_listeners:
            hostname = http_listener['hostName']
            if hostname is not None and http_listener['protocol'] == 'Https':
                expiration_date =  get_ssl_expiration(hostname)
                delta = expiration_date - datetime.date.today()

                if delta < datetime.timedelta(days=30):
                    result.append(hostname)

    return result


def main():
    '''Main function.'''
    load_dotenv()

    verify_az()
    login_to_az()

    hosts_requiring_renewal = []
    app_gateways = get_app_gateways()
    hosts_requiring_renewal = get_hosts_requiring_renewal(app_gateways)

    if len(hosts_requiring_renewal) > 0:
        # Planning to have this auto-renew with LE certs
        print('hosts requiring renewal:')
        print(hosts_requiring_renewal, sep='\n')
        sys.exit(1)

if __name__ == "__main__":
    main()
