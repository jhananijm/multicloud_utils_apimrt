from apimrt.cloud_meta.cloud_register import CloudMetaRegister
from apimrt.clouds.azure.azure_utils import AzureUtil
import requests


class AzureMeta(CloudMetaRegister):
    name = 'azure'

    def get_rg_name(self):
        param = {"api-version": "2021-12-13"}
        headers = {'Metadata': 'true'}
        data = requests.get("http://169.254.169.254/metadata/instance", params=param,
                            headers=headers).json()
        return data["compute"]["resourceGroupName"]

    def get_project_name(self):
        project_name = self.get_rg_name()
        suffixes = ("-rg", "-RG")
        for suffix in suffixes:
            if project_name.endswith(suffix):
                project_name = project_name.rstrip(suffix)
                return project_name

    def get_secrets(self):
        azure_util = AzureUtil(rg_name=self.get_rg_name())
        return azure_util.get_secrets(f"https://{self.get_project_name()}.vault.azure.net/")

    def get_project_secret_name(self):
        return f"{self.get_project_name()}"

    def update_secrets(self, key, value,secret_name=None):
        azure_util = AzureUtil(rg_name=self.get_rg_name())
        if secret_name is None:
            secret_name = f"https://{self.get_project_name()}.vault.azure.net/"
        else:
            secret_name = f"https://{secret_name}.vault.azure.net/"
        return azure_util.update_secrets(key,value,secret_name)

    def get_scaling_groups(self):
        azure_util = AzureUtil(rg_name=self.get_rg_name())
        return azure_util.get_scale_set_name_list()

    def update_image(self, image_id):
        updated_asg_list = []
        azure_util = AzureUtil(rg_name=self.get_rg_name())
        scaleset_list = azure_util.get_scale_set_name_list()
        for scale_set in scaleset_list:
            scaleset_tags = azure_util.get_scale_set_tags(scale_set)
            if scaleset_tags['Subtype'] in ['message-processor','router']:
                if "~" in image_id:
                    split_string = image_id.split("~")
                    image_rg, image_id = split_string[0], split_string[1]
                else:
                    image_rg = azure_util.get_image_rg_scaleset(scale_set)
                updated_asg_list.append(azure_util.update_image(scale_set, image_rg, image_id))
        return updated_asg_list

    def take_volume_snapshot(self, instance_ip):
        azure_util = AzureUtil(rg_name=self.get_rg_name())
        vm_name = azure_util.get_instance_name_from_ip(instance_ip, self.get_rg_name())
        return azure_util.take_volume_snapshot(vm_name)

    def get_instance_name(self, ip, project_name):
        rg_name = f"{project_name}-rg"
        azure_util = AzureUtil(rg_name=rg_name)
        return azure_util.get_instance_name_from_ip(ip, rg_name)

    def get_project_instance_name(self, ip):
        azure_util = AzureUtil(rg_name=self.get_rg_name())
        return azure_util.get_instance_name_from_ip(ip, self.get_rg_name())

    def get_instance_tags(self, instance_ip):
        azure_util = AzureUtil(rg_name=self.get_rg_name())
        instance_name = azure_util.get_instance_name_from_ip(instance_ip, self.get_rg_name())
        return azure_util.get_instance_tags(instance_name)

    def get_available_permissions(self):
        pass
