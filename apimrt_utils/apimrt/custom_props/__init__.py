import re
from typing import Tuple, List

import yaml

__PROTOCOLS_KEY__: str = "conf_load_balancing_load.balancing.driver.server.ssl.protocols"
__CIPHERS_KEY__: str = "conf_load_balancing_load.balancing.driver.server.ssl.ciphers"
__REQUIRED_SECTIONS__: Tuple[str, str, str] = (
    "tls_protocols",
    "enable_ciphers",
    "disable_ciphers",
)


class MissingSectionsException(Exception):
    pass


class CustomProps:

    def __init__(self, props_file: str, conf_file: str) -> None:
        """Initializes the custom props object.

        Args:
            props_file (str): The path to the properties file.
            conf_file (str): The path to the configuration YAML file.
        """

        self._props_file = props_file

        with open(conf_file, 'r') as yaml_file:
            self._conf = yaml.safe_load(yaml_file)

    def _filter_tls_ciphers(self, ciphers: List[str]) -> str:
        """Filters the specified ciphers using the configuration file, and returns a string containing the filtered
        ciphers separated with ':'.

        Args:
            ciphers (List[str]): The list of ciphers to filter.
        """

        if not all(v in self._conf for v in __REQUIRED_SECTIONS__):
            raise MissingSectionsException(
                f"Ensure all the following sections are present in config:\n{__REQUIRED_SECTIONS__}"
            )

        enable_set = set(self._conf["enable_ciphers"])
        disable_set = set(self._conf["disable_ciphers"])

        filtered_ciphers = [cipher for cipher in ciphers if cipher in enable_set or cipher not in disable_set]
        return ":".join(filtered_ciphers)

    def modify_tls_protocols(self):
        """Modifies the TLS protocols in the properties file.
        """

        with open(self._props_file, 'r') as props_file:
            content = props_file.read()

        protocols_pattern = rf"^{__PROTOCOLS_KEY__}=.*"
        protocols_match = re.search(protocols_pattern, content, re.MULTILINE)

        if protocols_match:
            protocols = " ".join(self._conf["tls_protocols"])
            modified_content = content.replace(protocols_match.group(0), f"{__PROTOCOLS_KEY__}={protocols}", 1)
            with open(self._props_file, 'w') as props_file:
                props_file.write(modified_content)
        else:
            protocols = " ".join(self._conf["tls_protocols"])
            with open(self._props_file, 'a') as props_file:
                props_file.write(f"{__PROTOCOLS_KEY__}={protocols}")

    def modify_tls_ciphers(self):
        """Modifies the TLS ciphers in the properties file.
        """

        with open(self._props_file, 'r') as props_file:
            content = props_file.read()

        ciphers_pattern = rf"^{__CIPHERS_KEY__}=.*"
        ciphers_match = re.search(ciphers_pattern, content, re.MULTILINE)

        if ciphers_match:
            ciphers = ciphers_match.group(0).strip().split('=')[1].split(':')
            filtered_ciphers = self._filter_tls_ciphers(ciphers)
            modified_content = content.replace(ciphers_match.group(0), f"{__CIPHERS_KEY__}={filtered_ciphers}", 1)
            with open(self._props_file, 'w') as props_file:
                props_file.write(modified_content)
        else:
            enable_ciphers = ":".join(self._conf["enable_ciphers"])
            with open(self._props_file, 'a') as props_file:
                props_file.write(f"{__CIPHERS_KEY__}={enable_ciphers}")

    def modify(self):
        """Modifies the properties file using the configuration file.
        """

        self.modify_tls_protocols()
        self.modify_tls_ciphers()
