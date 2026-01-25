from apimrt.cloud_meta.cloud_register import CloudMetaRegister
from apimrt.clouds.alibaba.alibaba_utils import AliBabaUtil
import requests
from typing import Any
import logging

logger = logging.getLogger(__name__)


class AlibabaMeta(CloudMetaRegister):
    name = 'alibaba'
    metadata_url = "http://100.100.100.200/latest/dynamic/instance-identity/document"
    metadata_sts_url = "http://100.100.100.200/latest/meta-data/ram/security-credentials/"

    def __init__(self) -> None:
        resp: Any = requests.get(self.metadata_url).json()
        self._METADATA = resp
        role: Any = requests.get(self.metadata_sts_url)
        if role.status_code == 200:
            sts_resp: Any = requests.get(
                f"{self.metadata_sts_url}{role.text}").json()
            self._METADATA_STS = sts_resp

    def get_region_id(self) -> str:
        return self._METADATA["region-id"]

    def get_sts_creds(self) -> str:
        return self._METADATA_STS["AccessKeyId"], self._METADATA_STS["AccessKeySecret"], self._METADATA_STS[
            "SecurityToken"]

    def get_ali_util(self):
        access_key_id, access_key_secret, security_token = self.get_sts_creds()
        return AliBabaUtil(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            security_token=security_token,
            region_id=self.get_region_id())

    def get_project_name(self):
        instance_id = self._METADATA["instance-id"]
        ali_util = self.get_ali_util()
        tags = ali_util.get_instance_tags(instance_id)
        return tags['Project']

    def get_secrets(self):
        ali_util = self.get_ali_util()
        return ali_util.get_secrets(f"{self.get_project_name()}-secret")

    def get_project_secret_name(self):
        return f"{self.get_project_name()}-secret"

    def update_secrets(self, key, value, secret_name=None):
        ali_util = self.get_ali_util()
        if secret_name is None:
            secret_name = self.get_project_secret_name()
        else:
            secret_name = f"{secret_name}"
        return ali_util.update_secrets(key,value,secret_name)

    def get_scaling_groups(self):
        ali_util = self.get_ali_util()
        asg_ids = ali_util.get_scaling_groups(project_name=self.get_project_name())
        return [ali_util.get_asg_name_from_asg_id(asg_id=asg_id) for asg_id in asg_ids]

    def update_image(self, image_id):
        ali_util = self.get_ali_util()
        return ali_util.update_image(image_id, self.get_project_name())

    def take_volume_snapshot(self, instance_ip):
        ali_util = self.get_ali_util()
        return ali_util.take_volume_snapshot(instance_ip, self.get_project_name())

    def get_instance_name(self, ip, project_name):
        ali_util = self.get_ali_util()
        instance_id = ali_util.get_instance_id_from_ip(ip, project_name)
        return ali_util.get_instance_name_from_id(instance_id)

    def get_project_instance_name(self, ip):
        ali_util = self.get_ali_util()
        instance_id = ali_util.get_instance_id_from_ip(ip, self.get_project_name())
        return ali_util.get_instance_name_from_id(instance_id)

    def get_instance_tags(self, instance_ip):
        ali_util = self.get_ali_util()
        project_name = self.get_project_name()
        instance_id = ali_util.get_instance_id_from_ip(instance_ip, project_name)
        return ali_util.get_instance_tags(instance_id)

    def get_role_name(self):
        role_name = requests.get(self.metadata_sts_url)
        return role_name.text

    def flatten_list(self, lst):
        flat_list = []
        for item in lst:
            if isinstance(item, list):
                flat_list.extend(self.flatten_list(item))
            else:
                flat_list.append(item)
        return flat_list

    def get_available_permissions(self):
        ali_util = self.get_ali_util()
        policy = ali_util.get_attached_policy(self.get_role_name())
        policy_document = ali_util.get_policy_document(policy)
        stmt = policy_document['Statement']
        permissions = []
        for itr in stmt:
            effect = itr.get('Effect', '')
            actions = itr.get('Action', [])
            resource = itr.get('Resource', None)
            if effect == "Allow" and resource:
                permissions.append(actions)
        return self.flatten_list(permissions)
