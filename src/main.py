# encoding: utf-8

from datetime import datetime
import ldap3
import logging
import sys
from os import environ
# from pprint import pprint

from prometheus_client import CollectorRegistry, Histogram, Counter, Gauge, push_to_gateway

from fileenv import fileenv

loglevel = environ.get('LOG_LEVEL', logging.DEBUG)
log = logging.getLogger(__name__)
log.setLevel(loglevel)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(fmt='[%(asctime)s: %(levelname)s] %(message)s'))
log.addHandler(handler)

# Load some config from ENV vars
ldap_uri = environ.get('LDAP_URI', 'ldap://192.168.1.70:3389')
baseDN=environ.get('BASE_DN','dc=georchestra,dc=org')
search_base = 'ou=users,{}'.format(baseDN)
# the geOrchestra role used to identify the users that should have an employeeNumber (used to connect to SSH)
match_role=environ.get('MATCH_ROLE', 'SSH_USER')
ldapadmin_passwd = fileenv('LDAPADMIN_PASSWORD', fallback='ldapadmin_pwd')

prom_pushgateway_uri = environ.get('PROM_PUSHGATEWAY_URI') # if not defined, it won't send metrics
# prom_pushgateway_uri = environ.get('PROM_PUSHGATEWAY_URI', 'localhost:9091')

# Prometheus metrics
registry = CollectorRegistry()
prom_nextEN = Gauge('next_employeeNumber', 'Next available value for employeeNumber LDAP attribute', registry=registry)
prom_addedEN = Counter('configured_employeeNumber_total', 'Number of users that have had the employeeNumber LDAP attribute configured', registry=registry)
prom_last_run = Gauge('job_last_success_unixtime', 'Last time the job was run', registry=registry)
prom_process_duration_seconds = Histogram('process_duration_seconds', 'Duration in seconds of the job process', registry=registry)


def get_next_employee_number(ldapconnection: ldap3.Connection):
    """
    Scan the LDAP directory for employeeNumber values. Look for the max value, and returns the following one (maxValue+1)
    :param ldapconnection: an ldap3 LDAP connection
    :return: employeeNumber value to use for next user
    """
    search_filter = '(employeeNumber=*)'
    attrs = ['employeeNumber']
    entry_generator = ldapconnection.extend.standard.paged_search(
        search_base=search_base, search_filter=search_filter,
        search_scope=ldap3.SUBTREE, attributes=attrs,
        paged_size=1000, generator=True)

    # Then get your results:
    maxEN = 1000
    pages = 0
    for entry in entry_generator:
        pages += 1
        maxEN = max(maxEN, int(entry['attributes']['employeeNumber']))
    return maxEN+1


def set_employee_number(ldapconnection: ldap3.Connection, nextEN: int):
    """
    Set an employeeNumber attribute to users that match the match_role pattern
    :param int: next available employee number
    :return: returns next available employeeNumber
    """
    search_filter = '(&(ObjectClass=InetOrgPerson)(memberOf=cn={},ou=roles,{})(!(employeeNumber=*)))'.format(match_role, baseDN)
    attrs = ['cn']
    ldapconnection.search(search_base, search_filter, attributes=attrs)
    # pprint(ldapconnection.entries)
    for entry in ldapconnection.entries:
        log.debug("Adding employeeNumber {} to user {}".format(nextEN, entry.cn))
        ldapconnection.modify('uid={},{}'.format(entry.cn, search_base),
             {'employeeNumber': [(ldap3.MODIFY_REPLACE, ['{}'.format(nextEN)])]})
        nextEN+=1
        log.debug(ldapconnection.result)
    return nextEN

@prom_process_duration_seconds.time()
def main():
    log.debug("Connecting to LDAP server {}".format(ldap_uri))
    server = ldap3.Server(ldap_uri)
    with ldap3.Connection(server, user='cn=admin,{}'.format(baseDN), password=ldapadmin_passwd, auto_bind=True) as conn:

        # Get employeeNumber to use
        nextEN = get_next_employee_number(conn)
        log.debug("Next available employeeNumber={}".format(nextEN))

        # Look for users belonging to SSH_USER role and not having an employeeNumber
        next_nextEN = set_employee_number(conn, nextEN)
        log.debug("Next available employeeNumber={}".format(next_nextEN))
        # close the connection
        conn.unbind()

        # Send metrics to prometheus pushgateway
        if prom_pushgateway_uri:
            prom_nextEN.set(next_nextEN)
            prom_addedEN.inc(next_nextEN-nextEN)
            prom_last_run.set_to_current_time()
            push_to_gateway(prom_pushgateway_uri, job='ldap-userid-sidecar', registry=registry)

        log.info("employeeNumbers up-to-date")

if __name__ == '__main__':
    main()

