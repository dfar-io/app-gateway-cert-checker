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
        'CLIENT_ID': os.getenv('CLIENT_ID'),
        'CLIENT_SECRET': os.getenv('CLIENT_SECRET'),
        'TENANT_ID': os.getenv('TENANT_ID')
    }

    for value in env_dict.items():
        if value[1] is None:
            raise OSError(f'{value[0]} environment variable not set.')

    return env_dict

env = get_env_vars()

def verify_az():
    '''Verifies az is set up.'''
    subprocess.run(["az", "--version"],
                    check=True,
                    stdout=subprocess.DEVNULL)

def login_to_az():
    '''Logs into az using service principal provided in env. variables'''
    try:
        subprocess.run(["az", "login", "--service-principal",
            "-u", env['CLIENT_ID'],
            "-p", env['CLIENT_SECRET'],
            "--tenant", env['TENANT_ID']],
            check=True,
            stdout=subprocess.DEVNULL)
    # Different behavior since we don't want to expose env. variables
    except subprocess.CalledProcessError:
        print('Failure when logging in.')
        sys.exit(1)


def get_subscriptions_ids():
    ''' Gets all subscriptions for an account '''
    subscription_ids = []
    cli_command = subprocess.run(["az", "account", "list"],
                             check=True,
                             capture_output=True)

    subscriptions_json = json.loads(cli_command.stdout)
    for subscription in subscriptions_json:
        subscription_ids.append(subscription['id'])

    return subscription_ids

def get_app_gateways(subscription_ids):
    '''Gets all app gateways for a collection of subscription IDs '''
    all_app_gateways = []
    for subscription_id in subscription_ids:
        try:
            result = subprocess.run(["az", "network", "application-gateway", "list",
                                    "--subscription", subscription_id],
                                    check=True,
                                    capture_output=True)
        except subprocess.CalledProcessError:
            print('Failure when gathering app gateways.')
            sys.exit(1)

        app_gateways = json.loads(result.stdout)
        for app_gateway in app_gateways:
            all_app_gateways.append(app_gateway)

    return all_app_gateways

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
        valid_https_listeners = list(filter(is_http_listener_valid, app_gateway['httpListeners']))

        for https_listener in valid_https_listeners:
            hostname = https_listener['hostName']
            expiration_date =  get_ssl_expiration(hostname)
            delta = expiration_date - datetime.date.today()

            if delta < datetime.timedelta(days=30):
                result.append(hostname)

    return result

def is_http_listener_valid(http_listener):
    ''' Given an HTTP Listener, confirms it havs a hostname and is HTTPS. '''
    hostname = http_listener['hostName']
    protocol = http_listener['protocol']
    return hostname is not None and protocol == 'Https'

def main():
    '''Main function.'''
    load_dotenv()

    verify_az()
    login_to_az()

    hosts_requiring_renewal = []
    subscription_ids = get_subscriptions_ids()
    app_gateways = get_app_gateways(subscription_ids)
    hosts_requiring_renewal = get_hosts_requiring_renewal(app_gateways)

    if len(hosts_requiring_renewal) > 0:
        # Planning to have this auto-renew with LE certs
        print('hosts requiring renewal:')
        print(hosts_requiring_renewal, sep='\n')
        sys.exit(1)

if __name__ == "__main__":
    main()
