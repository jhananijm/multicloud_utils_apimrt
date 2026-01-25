from apimrt.cloud_meta import CloudMetaRegister
import requests



class CC3Meta(CloudMetaRegister):
    name = 'cc3'

    def get_project_name(self):
        return "No project name defined for CC3"

    def get_secrets(self):
        pass

    def get_project_secret_name(self):
        pass

    def update_secrets(self, key, value, secret_name=None):
        pass

    def get_scaling_groups(self):
        pass

    def update_image(self,image_id):
        pass

    def take_volume_snapshot(self,instance_name):
        pass

    def get_instance_name(self,ip, project_name):
        pass
    
    def get_project_instance_name(self,ip):
        pass

    def get_instance_tags(self,instance_ip):
        pass



