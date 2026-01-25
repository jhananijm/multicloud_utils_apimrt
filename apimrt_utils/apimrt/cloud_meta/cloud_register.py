from abc import ABCMeta, abstractmethod
import apimrt
import yaml
import os

from typing import Dict, Optional, List, Tuple, Any, Union

clouds_factory = {}


class CloudMeta(ABCMeta):
    def __init__(cls, clsname, bases, methods):
        super().__init__(clsname, bases, methods)
        if hasattr(cls, 'name') and cls.name:
            clouds_factory[cls.name] = cls


class CloudMetaRegister(metaclass=CloudMeta):
    """
    Abstract class representing a cloud .
    All concrete cloud providers should implement this.
    """

    name = None

    @abstractmethod
    def get_project_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_secrets(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_available_permissions(self) -> List:
        raise NotImplementedError

    @abstractmethod
    def get_project_secret_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def update_secrets(self, key: str, value: str, secret_name=None) -> dict:
        """

        Args:
            key:
            value:
            secret_name: if secret name is not passed by default project secrets will be updated

        Returns:

        """
        raise NotImplementedError

    @abstractmethod
    def get_scaling_groups(self) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    def update_image(self, image_id) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_instance_name(self, ip, project_name):
        raise NotImplementedError

    @abstractmethod
    def get_project_instance_name(self, ip):
        return NotImplementedError

    @abstractmethod
    def get_instance_tags(self, instance_ip) -> dict:
        raise NotImplementedError

    @abstractmethod
    def take_volume_snapshot(self, instance_ip) -> List[str]:
        raise NotImplementedError

    def get_required_permissions(self) -> List:
        root_dir = os.path.dirname(apimrt.__file__)
        perm_data = []
        if self.name:
            with open(f"{root_dir}/clouds/{self.name}/data/permissions.yml", 'r') as perm_file:
                perm_data = yaml.safe_load(perm_file)
        return perm_data

    def get_missing_permissions(self) -> List:
        required_permissions = set(self.get_required_permissions())
        try:
            available_permissions = set(self.get_available_permissions())
            if required_permissions.issubset(available_permissions):
                return []
            else:
                missing_permissions = required_permissions.difference(available_permissions)
                return list(missing_permissions)
        except Exception as excp:  # sometimes roles might be missing to read the permissions
            return list(required_permissions)
