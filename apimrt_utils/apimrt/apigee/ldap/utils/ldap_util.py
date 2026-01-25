from ldap3 import Server, Connection, SUBTREE


class LdapUtil:
    def __init__(self, host='127.0.0.1', port=10389, username='cn=manager,dc=apigee,dc=com', password=None):
        self.ldap_url = f"ldap://{host}:{str(port)}"
        self.username = username
        self.password = password

    def is_authenticated(self) -> bool:

        """Validates the connectivity with ldap
         can be used for ldap password validation"""

        with Connection(Server(self.ldap_url), user=self.username, password=self.password) as conn:

            if not conn.bind():
                auth_flag = False
            else:
                auth_flag = True

        return auth_flag

    def get_server_id(self, username="cn=admin,cn=config") -> int:
        """
        Gives the current server id of connected LDAP server
        :return:
        """
        base_dn = 'cn=config'
        search_filter = '(objectClass=olcGlobal)'
        attribute = 'olcServerID'
        with Connection(Server(self.ldap_url), user=username, password=self.password) as conn:
            conn.search(base_dn, search_filter, attributes=[attribute], search_scope=SUBTREE)
            entry = conn.entries[0]
            olc_server_id = entry[attribute].value
        return olc_server_id

