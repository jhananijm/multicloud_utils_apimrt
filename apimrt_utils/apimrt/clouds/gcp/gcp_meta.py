from apimrt.cloud_meta import CloudMetaRegister
from apimrt.clouds.gcp.gcp_utils import GcpUtil
import requests
import json


class Gcp(CloudMetaRegister):
    name = 'gcp'
    metadata_url = "http://metadata.google.internal/computeMetadata/v1/"
    
    def get_project_name(self):
        headers = {}
        headers['Metadata-Flavor'] = 'Google'
        project_name = requests.get(f"{self.metadata_url}instance/attributes/project",
                                    headers=headers).text
        return project_name
    
    def get_service_account(self):
        headers = {}
        headers['Metadata-Flavor'] = 'Google'
        service_acc = requests.get(f"{self.metadata_url}instance/service-accounts/",
                                    headers=headers).text
        service_acc = list(filter(None, service_acc.split('\n')))
        service_acc = [item.rstrip('/') for item in service_acc if item]
        return service_acc
        
    
    def get_access_token(self):
        service_acc = self.get_service_account()
        service_acc = next((item for item in service_acc if item != 'default'), None)
        token = '{"access_token":""}'
        if service_acc != None:
            headers = {}
            headers['Metadata-Flavor'] = 'Google'
            token = requests.get(f"{self.metadata_url}instance/service-accounts/{service_acc}/token",
                                        headers=headers).text
        
        return (json.loads(token))['access_token']
    
    def get_global_project_id(self):
        headers = {}
        headers['Metadata-Flavor'] = 'Google'
        project_id = requests.get(f"{self.metadata_url}project/numeric-project-id",
                                    headers=headers).text
        return project_id

    def get_secrets(self):
        gcp_util = GcpUtil(project_id=self.get_global_project_id())
        return gcp_util.get_secrets(secret_id=f"{self.get_project_name()}-secrets")

    def get_project_secret_name(self):
        return f"{self.get_project_name()}-secrets"

    def update_secrets(self, key, value, secret_name = None):
        gcp_util = GcpUtil(project_id=self.get_global_project_id())
        if secret_name is None:
            secret_name = self.get_project_secret_name()
        else:
            secret_name = f"{self.get_global_project_id()}/secrets/{secret_name}"
        return gcp_util.update_secrets(key,value,secret_name)

    def get_scaling_groups(self):
        pass

    def update_image(self, image_id):
        pass

    def take_volume_snapshot(self, instance_ip):
        gcp_util = GcpUtil(project_id=self.get_global_project_id())
        return gcp_util.take_volume_snapshot(instance_ip, self.get_project_name())

    def get_instance_name(self, ip, project_name):
        gcp_util = GcpUtil(project_id=self.get_global_project_id())
        return gcp_util.get_instance_name(ip, project_name)
    
    def get_project_instance_name(self, ip):
        gcp_util = GcpUtil(project_id=self.get_global_project_id())
        return gcp_util.get_instance_name(ip, self.get_project_name())

    def get_instance_tags(self,  instance_ip):
        gcp_util = GcpUtil(project_id=self.get_global_project_id())
        return gcp_util.get_instance_tags(instance_ip, self.get_project_name())

    def get_available_permissions(self):
        pass


