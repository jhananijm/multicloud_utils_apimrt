"""TODO: docstring"""

from os.path import join
from pathlib import Path
from typing import Dict, Union, Tuple, Optional, List, Any

import re
import requests
import jinja2
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
import paramiko
from paramiko import SSHClient

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from apimrt.apigee.ldap.utils import LdapUtil
from apimrt.apigee.cassandra.utils import cass_util
from .templates import Templates

# TODO: docstring
_CompType = Literal[
    "zkcs",
    "ms",
    "router",
    "mp",
    "qpid",
    "pg",
    "ldap",
]

# TODO: docstring
# Following code does not working with Python 3.6, and has hence been commented.
# __COMPONENTS__: Tuple[str] = typing.get_args(_CompType)
__COMPONENTS__: Tuple[str] = (
    "zkcs",
    "ms",
    "router",
    "mp",
    "qpid",
    "pg",
    "ldap",
)

__TMP_CONFIG_PATH__: str = "/tmp/configFile"
__CONFIG_PATH__: str = "/opt/apigee/configFile"
__TMP_SSO_CONFIG_PATH__: str = "/tmp/sso_config_file"
__SSO_CONFIG_PATH__: str = "/opt/apigee/sso_config_file"


def is_pg_replica(client: SSHClient) -> bool:
    """Checks whether the current node is a postgres replica node.
    :return: Indicates whether the current node is a postgres replica node.
    :rtype: bool
    """

    _, stdout, _ = client.exec_command("{} {} {}".format(
        "/opt/apigee/apigee-service/bin/apigee-service",
        "apigee-postgresql",
        "postgres-check-standby",
    ))
    if not stdout:
        # If there was no output, we assume that the current node is not the replica node.
        return False

    matches: List[str] = re.findall(
        ".*slave/standby$", stdout.read().decode("utf-8"),
    )

    return bool(matches)


def handle_list_var(list_var: Optional[List[Any]]):
    """TODO: docstring"""

    if not list_var:
        return None

    return list_var[0]


def check_remote_file_kind(ssh: SSHClient, path: str) -> Optional[str]:
    """TODO: docstring"""

    try:
        _, stdout, _ = ssh.exec_command(f"cat {path}")
        data = stdout.read().decode("utf-8").splitlines()
        if len(data) == 0:
            return None
        if 'PRIVATE' in data[0]:
            return 'private_key'
        elif 'PUBLIC' in data[0]:
            return 'public_key'
        elif 'CERTIFICATE' in data[0]:
            return 'certificate'
        else:
            return None
    except FileNotFoundError:
        return None


def get_sso_info(ssh: SSHClient) -> Optional[Dict[str, str]]:
    """TODO: docstring"""

    _, stdout, _ = ssh.exec_command(
        "sudo cat /opt/apigee/token/application/sso.properties",
    )
    sso_out = stdout.read().decode("utf-8")
    _, stdout, _ = ssh.exec_command(
        "sudo cat /opt/apigee/token/application/ui.properties",
    )
    ui_out = stdout.read().decode("utf-8")

    try:
        SSO_SAML_IDP_METADATA_URL = [i.split('=')[1] for i in sso_out.splitlines() if
                                     'conf_login_saml_provider_metadataurl=' in i]
    except IndexError:
        SSO_SAML_IDP_METADATA_URL = None
    try:
        PG_USER = [i.split('=')[1] for i in sso_out.splitlines()
                   if 'conf_uaa_database_username=' in i]
    except IndexError:
        PG_USER = None
    try:
        IP2 = [i.split('=')[1].split('//')[1]
               for i in sso_out.splitlines() if 'conf_sso2_url=' in i]
    except IndexError:
        IP2 = None
    try:
        SSO_SAML_SERVICE_PROVIDER_PASSWORD = [i.split('=')[1].split('//')[1] for i in sso_out.splitlines() if
                                              'conf_login_service_provider_key_password=' in i]
    except IndexError:
        SSO_SAML_SERVICE_PROVIDER_PASSWORD = None
    try:
        SSO_ADMIN_SECRET = [i.split('=')[1].replace('"', '') for i in ui_out.splitlines() if
                            'conf_apigee-base_apigee.feature.ssoclientsecret=' in i]
    except IndexError:
        SSO_ADMIN_SECRET = None

    sso_dir = '/opt/apigee/customer/application/apigee-sso'
    jwt_keys_dir = sso_dir + '/jwt-keys'
    saml_sp_keys_dir = sso_dir + '/saml'
    _, stdout, _ = ssh.exec_command(f"ls {jwt_keys_dir}".format(jwt_keys_dir))
    jwt_keys_dir_files = stdout.read().decode("utf-8").splitlines()
    _, stdout, _ = ssh.exec_command(f"ls {saml_sp_keys_dir}")
    saml_sp_keys_dir_files = stdout.read().decode("utf-8").splitlines()
    if len(jwt_keys_dir_files) == 0 and len(saml_sp_keys_dir_files) == 0:
        print('Unable to find jwt key file path in SSO Server in {}'.format(sso_dir))
        return None

    SSO_JWT_SIGNING_KEY_FILEPATH = ""
    SSO_JWT_VERIFICATION_KEY_FILEPATH = ""
    SSO_SAML_SERVICE_PROVIDER_KEY = ""
    SSO_SAML_SERVICE_PROVIDER_CERTIFICATE = ""

    for each_file in jwt_keys_dir_files:
        abs_file_path = '{}/{}'.format(jwt_keys_dir, each_file)
        if check_remote_file_kind(ssh, abs_file_path) == 'private_key':
            SSO_JWT_SIGNING_KEY_FILEPATH = abs_file_path
        elif check_remote_file_kind(ssh, abs_file_path) == 'public_key':
            SSO_JWT_VERIFICATION_KEY_FILEPATH = abs_file_path

    for each_file in saml_sp_keys_dir_files:
        abs_file_path = '{}/{}'.format(saml_sp_keys_dir, each_file)
        if check_remote_file_kind(ssh, abs_file_path) == 'private_key':
            SSO_SAML_SERVICE_PROVIDER_KEY = abs_file_path
        elif check_remote_file_kind(ssh, abs_file_path) == 'certificate':
            SSO_SAML_SERVICE_PROVIDER_CERTIFICATE = abs_file_path

    info: Dict[str, str] = {
        'SSO_ADMIN_SECRET': handle_list_var(SSO_ADMIN_SECRET),
        'SSO_SAML_IDP_METADATA_URL': handle_list_var(SSO_SAML_IDP_METADATA_URL),
        'PG_USER': handle_list_var(PG_USER),
        'IP2': handle_list_var(IP2),
        'SSO_SAML_SERVICE_PROVIDER_PASSWORD': handle_list_var(SSO_SAML_SERVICE_PROVIDER_PASSWORD),
        'SSO_JWT_SIGNING_KEY_FILEPATH': SSO_JWT_SIGNING_KEY_FILEPATH,
        'SSO_JWT_VERIFICATION_KEY_FILEPATH': SSO_JWT_VERIFICATION_KEY_FILEPATH,
        'SSO_SAML_SERVICE_PROVIDER_KEY': SSO_SAML_SERVICE_PROVIDER_KEY,
        'SSO_SAML_SERVICE_PROVIDER_CERTIFICATE': SSO_SAML_SERVICE_PROVIDER_CERTIFICATE
    }

    return info


class SilentConfig:
    """TODO: docstring"""

    def __init__(
            self,
            inventory: Union[str, Path],
            extra_vars: Optional[Dict[str, str]] = None,
            output_dir: str = ".",
            ssh_user: str = "concourseci",
            ssh_private_key: str = "/etc/ansible/priv",
            ssh_port: int = 22,
    ) -> None:
        """TODO: docstring"""

        self._output_dir = output_dir
        self._ssh_user = ssh_user
        self._ssh_private_key = paramiko.RSAKey.from_private_key_file(
            ssh_private_key,
        )
        self._ssh_port = ssh_port

        dl = DataLoader()
        im = InventoryManager(loader=dl, sources=[inventory])
        vm = VariableManager(loader=dl, inventory=im)
        self._host_vars = vm.get_vars()
        if not extra_vars:
            extra_vars: Dict[str, str] = {}

        for comp in __COMPONENTS__:
            hosts = self._host_vars["groups"][comp]
            count = 1
            for host in hosts:
                extra_vars[f"{comp}_{count}"] = host
                count += 1

        ldap_1_util = LdapUtil(
            self._host_vars["groups"]["ldap"][0],
            password=extra_vars["ldap_password"]
        )
        ldap_2_util = LdapUtil(
            self._host_vars["groups"]["ldap"][1],
            password=extra_vars["ldap_password"]
        )

        dcs: List[str] = requests.get(
            "http://{}:8080/v1/regions".format(
                self._host_vars["groups"]["ms"][0],
            ),
            auth=(
                extra_vars["admin_email"],
                extra_vars["admin_password"],
            )
        ).json()
        mp_pod = None
        dc_name = None
        for dc in dcs:
            pods: List[str] = requests.get(
                "http://{}:8080/v1/regions/{}/pods".format(
                    self._host_vars["groups"]["ms"][0],
                    dc,
                ),
                auth=(
                    extra_vars["admin_email"],
                    extra_vars["admin_password"],
                ),
            ).json()
            for pod in pods:
                servers: List[Dict[str, Any]] = requests.get(
                    "http://{}:8080/v1/regions/{}/pods/{}/servers".format(
                        self._host_vars["groups"]["ms"][0],
                        dc,
                        pod,
                    ),
                    auth=(
                        extra_vars["admin_email"],
                        extra_vars["admin_password"],
                    ),
                ).json()
                for server in servers:
                    if "message-processor" in server["type"]:
                        mp_pod = server["pod"]
                        dc_name = server["region"]
                        break
                if mp_pod:
                    break
            if dc_name:
                break

        # retrieving cassandra dc_number and rack_number
        cass = cass_util.CassUtil(self._host_vars["groups"]["zkcs"][0])
        cass_dc_number = cass.get_dc_number()
        cass_rack_number = cass.get_rack_number()

        pg_master = self._host_vars["groups"]["pg"][0]
        pg_standby = self._host_vars["groups"]["pg"][1]
        pg_ssh_client = SSHClient()
        pg_ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        pg_ssh_client.connect(
            pg_master,
            port=self._ssh_port,
            username=self._ssh_user,
            pkey=self._ssh_private_key,
        )
        if is_pg_replica(pg_ssh_client):
            # Swap master and standby
            pg_master, pg_standby = pg_standby, pg_master

        self._files: Dict[str, Dict[str, str]] = {
            "MS_1": {
                "ms_ip": self._host_vars["groups"]["ms"][0],
                "ldap_ip": self._host_vars["groups"]["ldap"][0],
                "pgm_ip": pg_master,
                "pgs_ip": pg_standby,
                "pod_name": mp_pod,
                "dc_name": dc_name,
                "cass_dc_number": cass_dc_number,
                "cass_rack_number": cass_rack_number,
                **extra_vars,
            },
            "MS_2": {
                "ms_ip": self._host_vars["groups"]["ms"][1],
                "ldap_ip": self._host_vars["groups"]["ldap"][1],
                "pgm_ip": pg_master,
                "pgs_ip": pg_standby,
                "pod_name": mp_pod,
                "dc_name": dc_name,
                "cass_dc_number": cass_dc_number,
                "cass_rack_number": cass_rack_number,
                **extra_vars,
            },
            "LDAP_1": {
                "ms_ip": self._host_vars["groups"]["ms"][0],
                "ldap_ip": self._host_vars["groups"]["ldap"][0],
                "ldap_sid": ldap_1_util.get_server_id(),
                "ldap_peer": self._host_vars["groups"]["ldap"][1],
                "pgm_ip": pg_master,
                "pgs_ip": pg_standby,
                "pod_name": mp_pod,
                "dc_name": dc_name,
                **extra_vars,
            },
            "LDAP_2": {
                "ms_ip": self._host_vars["groups"]["ms"][1],
                "ldap_ip": self._host_vars["groups"]["ldap"][1],
                "ldap_sid": ldap_2_util.get_server_id(),
                "ldap_peer": self._host_vars["groups"]["ldap"][0],
                "pgm_ip": pg_master,
                "pgs_ip": pg_standby,
                "pod_name": mp_pod,
                "dc_name": dc_name,
                **extra_vars,
            },
            "PG": {
                "ms_ip": self._host_vars["groups"]["ms"][0],
                "ldap_ip": self._host_vars["groups"]["ldap"][0],
                "pgm_ip": pg_master,
                "pgs_ip": pg_standby,
                "pod_name": mp_pod,
                "dc_name": dc_name,
                "cass_dc_number": cass_dc_number,
                "cass_rack_number": cass_rack_number,
                **extra_vars,
            },
            "ALL": {
                "ms_ip": self._host_vars["groups"]["ms"][0],
                "ldap_ip": self._host_vars["groups"]["ldap"][0],
                "pgm_ip": pg_master,
                "pgs_ip": pg_standby,
                "pod_name": mp_pod,
                "dc_name": dc_name,
                "cass_dc_number" : cass_dc_number,
                "cass_rack_number" : cass_rack_number,
                **extra_vars,
            },
        }

        i = 1
        for ms in self._host_vars["groups"]["sso"]:
            ms_ssh_client = SSHClient()
            ms_ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ms_ssh_client.connect(
                ms,
                username=self._ssh_user,
                pkey=self._ssh_private_key,
                port=self._ssh_port,
            )
            sso_info = get_sso_info(ms_ssh_client)
            self._files[f"SSO_{i}"] = {
                "ms_ip": ms,
                "pg_ip": pg_master,
                "admin_email": extra_vars["admin_email"],
                "admin_password": extra_vars["admin_password"],
                "pg_password": extra_vars["pg_password"],
                **sso_info,
            }
            i += 1

        self._configs: Dict[str, str] = {}

        for file in self._files:
            environment = jinja2.Environment()
            template = Templates.ALL
            if file in ("LDAP_1", "LDAP_2"):
                template = Templates.LDAP
            if file.startswith("SSO_"):
                template = Templates.SSO
            tpl: jinja2.Template = environment.from_string(str(template))
            self._configs[file] = tpl.render(self._files[file])

    def render(self):
        """TODO: docstring"""

        for config in self._configs:
            with open(
                    join(self._output_dir, config),
                    "w",
                    encoding="utf8",
            ) as _f:
                _f.write(self._configs[config])

    def upload(self):
        """TODO: docstring"""

        # ZKCS
        for host in self._host_vars["groups"]["zkcs"]:
            ssh_client = SSHClient()
            ssh_client.set_missing_host_key_policy(
                paramiko.AutoAddPolicy()
            )
            ssh_client.connect(
                host,
                port=self._ssh_port,
                username=self._ssh_user,
                pkey=self._ssh_private_key,
            )
            sftp_client = ssh_client.open_sftp()
            sftp_client.put(
                join(self._output_dir, "ALL"),
                __TMP_CONFIG_PATH__,
            )
            ssh_client.exec_command(
                f"sudo cp {__TMP_CONFIG_PATH__} {__CONFIG_PATH__}",
            )

        # MP
        for host in self._host_vars["groups"]["mp"]:
            ssh_client = SSHClient()
            ssh_client.set_missing_host_key_policy(
                paramiko.AutoAddPolicy()
            )
            ssh_client.connect(
                host,
                port=self._ssh_port,
                username=self._ssh_user,
                pkey=self._ssh_private_key,
            )
            sftp_client = ssh_client.open_sftp()
            sftp_client.put(
                join(self._output_dir, "ALL"),
                __TMP_CONFIG_PATH__,
            )
            ssh_client.exec_command(
                f"sudo cp {__TMP_CONFIG_PATH__} {__CONFIG_PATH__}",
            )

        # ROUTER
        for host in self._host_vars["groups"]["router"]:
            ssh_client = SSHClient()
            ssh_client.set_missing_host_key_policy(
                paramiko.AutoAddPolicy()
            )
            ssh_client.connect(
                host,
                port=self._ssh_port,
                username=self._ssh_user,
                pkey=self._ssh_private_key,
            )
            sftp_client = ssh_client.open_sftp()
            sftp_client.put(
                join(self._output_dir, "ALL"),
                __TMP_CONFIG_PATH__,
            )
            ssh_client.exec_command(
                f"sudo cp {__TMP_CONFIG_PATH__} {__CONFIG_PATH__}",
            )

        # QPID
        for host in self._host_vars["groups"]["qpid"]:
            ssh_client = SSHClient()
            ssh_client.set_missing_host_key_policy(
                paramiko.AutoAddPolicy()
            )
            ssh_client.connect(
                host,
                port=self._ssh_port,
                username=self._ssh_user,
                pkey=self._ssh_private_key,
            )
            sftp_client = ssh_client.open_sftp()
            sftp_client.put(
                join(self._output_dir, "ALL"),
                __TMP_CONFIG_PATH__,
            )
            ssh_client.exec_command(
                f"sudo cp {__TMP_CONFIG_PATH__} {__CONFIG_PATH__}",
            )

        # SSO
        i = 1
        for host in self._host_vars["groups"]["sso"]:
            ssh_client = SSHClient()
            ssh_client.set_missing_host_key_policy(
                paramiko.AutoAddPolicy()
            )
            ssh_client.connect(
                host,
                port=self._ssh_port,
                username=self._ssh_user,
                pkey=self._ssh_private_key,
            )
            sftp_client = ssh_client.open_sftp()
            sftp_client.put(
                join(self._output_dir, f"SSO_{i}"),
                __TMP_SSO_CONFIG_PATH__,
            )
            ssh_client.exec_command(
                f"sudo cp {__TMP_SSO_CONFIG_PATH__} {__SSO_CONFIG_PATH__}",
            )
            i += 1

        # MS
        ms1_client = SSHClient()
        ms1_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ms1_client.connect(
            self._host_vars["groups"]["ms"][0],
            port=self._ssh_port,
            username=self._ssh_user,
            pkey=self._ssh_private_key,
        )
        sftp_client = ms1_client.open_sftp()
        sftp_client.put(
            join(self._output_dir, "MS_1"),
            __TMP_CONFIG_PATH__,
        )
        ms1_client.exec_command(
            f"sudo cp {__TMP_CONFIG_PATH__} {__CONFIG_PATH__}",
        )

        ms2_client = SSHClient()
        ms2_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ms2_client.connect(
            self._host_vars["groups"]["ms"][1],
            port=self._ssh_port,
            username=self._ssh_user,
            pkey=self._ssh_private_key,
        )
        sftp_client = ms2_client.open_sftp()
        sftp_client.put(
            join(self._output_dir, "MS_2"),
            __TMP_CONFIG_PATH__,
        )
        ms2_client.exec_command(
            f"sudo cp {__TMP_CONFIG_PATH__} {__CONFIG_PATH__}",
        )

        # PG
        pg1_client = SSHClient()
        pg1_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        pg1_client.connect(
            self._host_vars["groups"]["pg"][0],
            port=self._ssh_port,
            username=self._ssh_user,
            pkey=self._ssh_private_key,
        )
        sftp_client = pg1_client.open_sftp()
        sftp_client.put(
            join(self._output_dir, "PG"),
            __TMP_CONFIG_PATH__,
        )
        pg1_client.exec_command(
            f"sudo cp {__TMP_CONFIG_PATH__} {__CONFIG_PATH__}",
        )

        pg2_client = SSHClient()
        pg2_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        pg2_client.connect(
            self._host_vars["groups"]["pg"][1],
            port=self._ssh_port,
            username=self._ssh_user,
            pkey=self._ssh_private_key,
        )
        sftp_client = pg2_client.open_sftp()
        sftp_client.put(
            join(self._output_dir, "PG"),
            __TMP_CONFIG_PATH__,
        )
        pg2_client.exec_command(
            f"sudo cp {__TMP_CONFIG_PATH__} {__CONFIG_PATH__}",
        )

        # LDAP
        ldap1_client = SSHClient()
        ldap1_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ldap1_client.connect(
            self._host_vars["groups"]["ldap"][0],
            port=self._ssh_port,
            username=self._ssh_user,
            pkey=self._ssh_private_key,
        )
        sftp_client = ldap1_client.open_sftp()
        sftp_client.put(
            join(self._output_dir, "LDAP_1"),
            __TMP_CONFIG_PATH__,
        )
        ldap1_client.exec_command(
            f"sudo cp {__TMP_CONFIG_PATH__} {__CONFIG_PATH__}",
        )

        ldap2_client = SSHClient()
        ldap2_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ldap2_client.connect(
            self._host_vars["groups"]["ldap"][1],
            port=self._ssh_port,
            username=self._ssh_user,
            pkey=self._ssh_private_key,
        )
        sftp_client = ldap2_client.open_sftp()
        sftp_client.put(
            join(self._output_dir, "LDAP_2"),
            __TMP_CONFIG_PATH__,
        )
        ldap2_client.exec_command(
            f"sudo cp {__TMP_CONFIG_PATH__} {__CONFIG_PATH__}",
        )
