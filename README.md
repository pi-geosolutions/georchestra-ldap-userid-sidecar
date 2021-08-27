# LDAP user id sidecar

This script is meant to be run as a cronjob besides the geOrchestra LDAP container,
in order to set the employeeNumber LDAP attribute for any user belonging to
SSH_USER role, and not having one already.

The employeeNumber attribute is used by the [ssh console container](https://github.com/pi-geosolutions/docker-ssh-ldappam) designed for PSK/KSK slovak regions.
It needs to start above 1000, since it is used to provide the users UIDs.

Available environment variables:
* `LDAP_URI`: the address of the LDAP server, including the port number. Defaults to `ldap://localhost:3389`
* `BASE_DN`: the base DN for the LDAP records. Defaults to `dc=georchestra,dc=org`
* `MATCH_ROLE`: the role against the users are searched for. Defaults to `SSH_USER`
* `PROM_PUSHGATEWAY_URI`: the prometheus pushgateway address, including the port number, e.g. `localhost:9091`.
If not defined, the app won't try to push the metrics
* `LDAPADMIN_PASSWORD`: the LDAP admin password. Can also be provided as a secret (recommended way). Use
`LDAPADMIN_PASSWORD_FILE` to point to the location of the secret file
