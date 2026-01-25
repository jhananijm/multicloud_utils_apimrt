from apimrt.cloud_meta import CloudMetaRegister
import requests
from apimrt.clouds.aws.aws_utils import AwsUtil


class AwsMeta(CloudMetaRegister):
    name = 'aws'

    metadata_url = "http://169.254.169.254/latest/meta-data"

    def get_region(self):
        headers = {}
        return requests.get(f"{self.metadata_url}/placement/region").text

    def get_project_name(self):
        headers = {}
        return requests.get(
            f"{self.metadata_url}/tags/instance/Project"
        ).text

    def get_secrets(self):
        aws_obj = AwsUtil(self.get_region())
        return aws_obj.get_secrets(f"{self.get_project_name()}-secret")

    def get_instance_profile_name(self):
        response = requests.get(f'{self.metadata_url}/iam/info')
        instance_profile_arn = response.json()['InstanceProfileArn']
        instance_profile_name = instance_profile_arn.split('/')[-1]
        return instance_profile_name

    def get_role_name(self):
        instance_profile_name = self.get_instance_profile_name()
        aws_obj = AwsUtil(self.get_region())
        response = aws_obj.get_instance_profile(instance_profile_name=instance_profile_name)
        role_name = response['InstanceProfile']['Roles'][0]['RoleName']
        return role_name

    def get_policy_map(self):
        policy_map = {}
        role_name = self.get_role_name()
        aws_obj = AwsUtil(self.get_region())
        policy_paginator = aws_obj.get_attached_policy_paginator()
        role_policies = []
        for response in policy_paginator.paginate(RoleName=role_name):
            role_policies.extend(response.get('AttachedPolicies'))
            policy_map.update({role_name: role_policies})
        return policy_map

    def get_available_permissions(self):
        aws_obj = AwsUtil(self.get_region())
        policy_map = self.get_policy_map()
        permissions = []
        for role, policies in policy_map.items():
            policy_document = aws_obj.get_policy_document(policy_map[role][0]['PolicyArn'])
            if 'Statement' in policy_document:
                for statement in policy_document['Statement']:
                    effect = statement.get('Effect', '')
                    actions = statement.get('Action', [])
                    resource = statement.get('Resource', None)
                    if effect == "Allow" and resource:
                        permissions.extend(actions)
        return permissions

    def get_project_secret_name(self):
        return f"{self.get_project_name()}-secret"
    
    def update_secrets(self,key,value,secret_name=None):
        aws_obj = AwsUtil(self.get_region())
        if secret_name is None:
            secret_name = self.get_project_secret_name()
        return aws_obj.update_secrets(key,value,secret_name)

    def get_scaling_groups(self):
        aws_obj = AwsUtil(self.get_region())
        return aws_obj.get_asg_list_by_tag('Project', self.get_project_name())

    def update_image(self, image_id):
        project_name = self.get_project_name()
        aws_obj = AwsUtil(self.get_region())
        return aws_obj.update_image(project_name, image_id)

    def take_volume_snapshot(self, instance_ip):
        project = self.get_project_name()
        aws_obj = AwsUtil(self.get_region())
        instance_id = aws_obj.get_instance_id(instance_ip, project)
        return aws_obj.take_snapshot(instance_id, project)

    def get_instance_name(self, ip, project_name):
        aws_obj = AwsUtil(self.get_region())
        return aws_obj.get_instance_name_from_private_ip(ip,project_name)

    def get_project_instance_name(self, ip):
        project = self.get_project_name()
        aws_obj = AwsUtil(self.get_region())
        return aws_obj.get_instance_name_from_private_ip(ip,project)

    def get_instance_tags(self, instance_ip):
        aws_obj = AwsUtil(self.get_region())
        project = self.get_project_name()
        instance_id = aws_obj.get_instance_id(instance_ip,project)
        return aws_obj.get_instance_tags(instance_id)