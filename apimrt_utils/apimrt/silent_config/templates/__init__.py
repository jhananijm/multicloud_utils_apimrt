from enum import Enum


class Templates(Enum):
    """TODO: docstring"""

    ALL: str = """HOSTIP=$(hostname -i)
ENABLE_SYSTEM_CHECK=n
ADMIN_EMAIL={{ admin_email }}
APIGEE_ADMINPW={{ admin_password }}
LICENSE_FILE=/opt/apigee/sap_perpetual.txt
# First Management Server on IP6
MSIP={{ ms_ip }}
USE_LDAP_REMOTE_HOST=y
LDAP_HOST={{ ldap_ip }}
LDAP_PORT=10389
APIGEE_LDAPPW={{ ldap_password }}
MP_POD={{ pod_name }}
REGION={{ dc_name }}
ZK_HOSTS="{{ zkcs_1 }} {{ zkcs_2 }} {{ zkcs_3 }}"
ZK_CLIENT_HOSTS="{{ zkcs_1 }} {{ zkcs_2 }} {{ zkcs_3 }}"
# Must use IP addresses for CASS_HOSTS, not DNS names.
CASS_HOSTS="{{ zkcs_1 }}:{{ cass_dc_number }},{{ cass_rack_number }} {{ zkcs_2 }}:{{ cass_dc_number }},{{ cass_rack_number }} {{ zkcs_3 }}:{{ cass_dc_number }},{{ cass_rack_number }}"
# Default is postgres
PG_PWD={{ pg_password }}
PG_MASTER={{ pgm_ip }}
PG_STANDBY={{ pgs_ip }}
SKIP_SMTP=y
SMTPHOST=smtp.example.com
SMTPUSER=smtp@example.com
# omit for no username
SMTPPASSWORD={{ admin_password }}
# omit for no password
SMTPSSL=n
SMTPPORT=25
SMTPMAILFROM="{{ admin_email }}"
BRAND=sap
"""

    LDAP: str = """# For OpenLDAP on IP4 and IP5
HOSTIP=$(hostname -i)
ENABLE_SYSTEM_CHECK=n
ADMIN_EMAIL={{ admin_email }}
APIGEE_ADMINPW={{ admin_password }}
LICENSE_FILE=/opt/apigee/sap_perpetual.txt
MSIP={{ ms_ip }}
USE_LDAP_REMOTE_HOST=n
LDAP_TYPE=2
LDAP_SID={{ ldap_sid }}
LDAP_PEER={{ ldap_peer }}
APIGEE_LDAPPW={{ ldap_password }}
BRAND=sap
"""

    SSO: str = """IP1={{ ms_ip }}
IP2={{ IP2 }}
MSIP=$IP1
MGMT_PORT=8080
ADMIN_EMAIL={{ admin_email }}
APIGEE_ADMINPW={{ admin_password }}
LICENSE_FILE=/opt/apigee/sap_perpetual.txt
MS_SCHEME=http
PG_HOST={{ pg_ip }}
PG_PORT=5432
PG_USER={{ PG_USER }}
PG_PWD={{ pg_password }}
SSO_PROFILE="saml"
SSO_PUBLIC_URL_HOSTNAME=$IP2
SSO_PUBLIC_URL_PORT=443
SSO_TOMCAT_PROFILE=SSL_PROXY
SSO_TOMCAT_PROXY_PORT=443
SSO_TOMCAT_PORT=9099
SSO_PUBLIC_URL_PORT=443
SSO_PUBLIC_URL_SCHEME=https
SSO_ADMIN_NAME=ssoadmin
SSO_ADMIN_SECRET={{ SSO_ADMIN_SECRET }}
SSO_SAML_SIGN_REQUEST=y
SSO_JWT_SIGNING_KEY_FILEPATH={{ SSO_JWT_SIGNING_KEY_FILEPATH }}
SSO_JWT_VERIFICATION_KEY_FILEPATH={{ SSO_JWT_VERIFICATION_KEY_FILEPATH }}
SSO_SAML_IDP_NAME=adfs
SSO_SAML_IDP_LOGIN_TEXT="Please log in to your IDP"
SSO_SAML_IDP_METADATA_URL={{ SSO_SAML_IDP_METADATA_URL }}
SSO_SAML_IDPMETAURL_SKIPSSLVALIDATION=n
SSO_SAML_SERVICE_PROVIDER_PASSWORD={{ SSO_SAML_SERVICE_PROVIDER_PASSWORD }}
SSO_SAML_SERVICE_PROVIDER_KEY={{ SSO_SAML_SERVICE_PROVIDER_KEY }}
SSO_SAML_SERVICE_PROVIDER_CERTIFICATE={{ SSO_SAML_SERVICE_PROVIDER_CERTIFICATE }}
SKIP_SMTP=y
SMTPMAILFROM={{ admin_email }}"""

    def __str__(self) -> str:
        """TODO: docstring"""

        return self.value

    def __eq__(self, other: object) -> bool:
        """TODO: docstring"""

        return self.value == other
