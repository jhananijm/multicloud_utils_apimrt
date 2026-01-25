import json
import base64
import time
import oss2
import datetime
from datetime import timezone
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.auth import credentials
from alibabacloud_credentials.models import Config
from alibabacloud_credentials.client import Client
from aliyunsdkkms.request.v20160120.GetSecretValueRequest import GetSecretValueRequest
from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest
from aliyunsdkecs.request.v20140526.CreateSnapshotRequest import CreateSnapshotRequest
from aliyunsdkecs.request.v20140526.DescribeDisksRequest import DescribeDisksRequest
from aliyunsdkess.request.v20140828.CompleteLifecycleActionRequest import CompleteLifecycleActionRequest
from aliyunsdkess.request.v20140828.DescribeScalingGroupsRequest import DescribeScalingGroupsRequest
from aliyunsdkess.request.v20140828.DescribeScalingInstancesRequest import DescribeScalingInstancesRequest
from aliyunsdkess.request.v20140828.ListTagResourcesRequest import ListTagResourcesRequest
from aliyunsdkess.request.v20140828.DescribeScalingConfigurationsRequest import DescribeScalingConfigurationsRequest
from aliyunsdkess.request.v20140828.ModifyScalingConfigurationRequest import ModifyScalingConfigurationRequest
from aliyunsdkram.request.v20150501.ListPoliciesForRoleRequest import ListPoliciesForRoleRequest
from aliyunsdkram.request.v20150501.GetPolicyRequest import GetPolicyRequest
from aliyunsdkecs.request.v20140526.DescribeSnapshotsRequest import DescribeSnapshotsRequest
from aliyunsdkkms.request.v20160120 import UpdateSecretRequest
from oss2.exceptions import NoSuchBucket
import logging

logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

class AliBabaUtil:

    def __init__(
            self,
            region_id: str,
            access_key_id: str,
            access_key_secret: str,
            security_token: str) -> str:
        '''
        :param region: Region of landscape
        :param access_key_id: Ali Cloud Access Key
        :param access_key_secret: Ali Cloud Access Key Secret
        :param security_token: Ali Cloud STS Token
        '''
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.security_token = security_token
        self.region_id = region_id

    @property
    def get_client(self):
        try:
            credential = credentials.StsTokenCredential(
                self.access_key_id, self.access_key_secret, self.security_token
            )
            return AcsClient(credential=credential, region_id=self.region_id)
        except Exception as excp:
            logger.error(f"UnexpectedError: {excp}")
            raise excp

    def get_oss_client(self, bucket_name):
        oss_credential = oss2.StsAuth(
            self.access_key_id, self.access_key_secret, self.security_token
        )
        endpoint = f"https://oss-{self.region_id}.aliyuncs.com"
        return oss2.Bucket(oss_credential, endpoint, bucket_name)

    def get_sts_creds(self, role_name, role_type='ecs_ram_role'):
        '''
            :param role_name: Optional. The name of the RAM role. 
            :param role_type: The type of the credential, default is set to ecs_ram_role.
            If this parameter is not specified, 
            the role name is automatically obtained. 
            We recommend that you set the parameter to reduce the number of requests.
            This function can be used with in a VM with proper role attached.
        '''
        try:
            ali_client = Config(
                type=role_type,
                role_name=role_name)
            cred = Client(ali_client)
            access_key_id = cred.get_access_key_id()
            access_key_secret = cred.get_access_key_secret()
            security_token = cred.get_security_token()
            return access_key_id, access_key_secret, security_token
        except Exception as excp:
            logger.error(f"UnexpectedError: {excp}")
            raise excp

    def _send_request(self, request):
        request.set_accept_format('json')
        try:
            response_str = self.get_client.do_action_with_exception(request)
            return json.loads(response_str.decode("UTF-8"))
        except Exception as excp:
            logger.error(f"UnexpectedError: {excp}")
            raise excp

    def get_secrets(self, secret_name: str):
        try:
            request = GetSecretValueRequest()
            request.set_SecretName(secret_name)
            response = self._send_request(request)
            try:
                secrets = json.loads(base64.b64decode(response['SecretData']))
            except Exception:
                secrets = response['SecretData']
            return json.loads(secrets)
        except Exception as excp:
            logger.error(f"UnexpectedError: {excp}")
            raise excp

    def update_secrets(self, key, value, secret_name: str):
        try:
            #client = AcsClient(region_id=self.region_id)
            request = UpdateSecretRequest.UpdateSecretRequest()
            request.set_SecretName(secret_name)
            response = self._send_request(request)
            updated_secret = request.set_SecretData(json.dumps({"value": value}))
            self.get_client.do_action_with_exception(updated_secret)
    
            print("Secret value updated successfully!")
        except Exception as excp:
            logger.error(f"UnexpectedError: {excp}")
            raise excp


    def get_instance_private_ip(self, instance_id: str) -> str:
        try:
            request = DescribeInstancesRequest()
            request.set_InstanceIds([instance_id])
            response = self._send_request(request)
            if response.get('Instances').get('Instance'):
                return (
                    response.get('Instances')
                    .get('Instance')[0]
                    .get('VpcAttributes')
                    .get('PrivateIpAddress')
                    .get('IpAddress')[0]
                )
            else:
                logger.error(f"Instance with ID {instance_id} not found")
        except Exception as excp:
            logger.error(f"UnexpectedError: {excp}")
            raise excp

    def get_instance_name_from_id(self,instance_id):
        try:
            request = DescribeInstancesRequest()
            request.set_PageSize(100)
            request.set_InstanceIds([instance_id])
            response = self._send_request(request)
            instances = response.get('Instances').get('Instance')
            if instances:
                return instances[0].get('InstanceName')
            else: 
                 logger.error(f"Instance with ID {instance_id} not found") 
        except Exception as excp:
            logger.error(f"UnexpectedError: {excp}")
            raise excp

    def get_instance_id_from_ip(self,instance_ip, project_name):
        try:
            request = DescribeInstancesRequest()
            request.set_PageSize(100)
            request.set_PageNumber(1)
            request.set_PrivateIpAddresses(json.dumps([instance_ip]))
            request.set_Tags([{'Key': 'Project','Value': project_name}])
            response = self._send_request(request)
            return response.get('Instances').get('Instance')[0]['InstanceId']

        except Exception as e:
            logger.error(f"UnexpectedError: {e}")
            raise e

    def get_instance_tags(self, instance_id: str) -> str:
        instance_tags = {}
        try:
            request = DescribeInstancesRequest()
            request.set_InstanceIds([instance_id])
            response = self._send_request(request)
            if response.get('Instances').get('Instance')[0].get('Tags').get('Tag'):
                for tags_dict in response.get('Instances').get('Instance')[0].get('Tags').get('Tag'):
                    instance_tags[tags_dict['TagKey']] = tags_dict['TagValue']
                return instance_tags
            else:
                logger.error(f"Instance with ID {instance_id} not found")
        except Exception as excp:
            logger.error(f"UnexpectedError: {excp}")
            raise excp

    def complete_lifecycle_action(self, LifecycleHookId: str,
                                  LifecycleActionToken: str,
                                  LifecycleActionResult: str = 'CONTINUE') -> bool:
        """
        :param LifecycleHookId:
        :param LifecycleActionToken:
        :param LifecycleActionResult:
        :return:
        """
        request = CompleteLifecycleActionRequest()
        request.set_LifecycleHookId(LifecycleHookId)
        request.set_LifecycleActionToken(LifecycleActionToken)
        request.set_LifecycleActionResult(LifecycleActionResult)
        response = self._send_request(request)
        if response != None:
            logger.info(f"Lifecycle {LifecycleActionResult} Successfully")
            return True
        logger.error(f"Lifecycle {LifecycleActionResult} Unsuccessful")
        return False

    def get_asg_id_from_asg_name(self, asg_name):
        request = DescribeScalingGroupsRequest()
        request.set_ScalingGroupName(asg_name)
        response = self._send_request(request)
        if len(response["ScalingGroups"]["ScalingGroup"]) > 1:
            logger.error("More than one scaling group found")
            raise ValueError
        elif len(response["ScalingGroups"]["ScalingGroup"]) < 1:
            logger.error("Scaling group not found")
            raise ValueError
        return response["ScalingGroups"]["ScalingGroup"][0]["ScalingGroupId"]
    
    def get_asg_name_from_asg_id(self, asg_id):
        request = DescribeScalingGroupsRequest()
        request.set_ScalingGroupIds([asg_id])
        response = self._send_request(request)
        if len(response["ScalingGroups"]["ScalingGroup"]) > 1:
            logger.error("More than one scaling group found")
            raise ValueError
        elif len(response["ScalingGroups"]["ScalingGroup"]) < 1:
            logger.error("Scaling group not found")
            raise ValueError
        return response["ScalingGroups"]["ScalingGroup"][0]["ScalingGroupName"]

    def get_instances_id_from_asg(self, asg_id):
        request = DescribeScalingInstancesRequest()
        request.set_ScalingGroupId(asg_id)
        response = self._send_request(request)
        return [inst_dict['InstanceId'] for inst_dict in response["ScalingInstances"]["ScalingInstance"]]

    def get_asg_tags(self, asg_id):
        tags_asg = {}
        request = ListTagResourcesRequest()
        request.set_ResourceIds([asg_id])
        request.set_ResourceType('scalinggroup')
        response = self._send_request(request)
        for inst_dict in response["TagResources"]["TagResource"]:
            tags_asg[inst_dict['TagKey']] = inst_dict['TagValue']
        return tags_asg

    def does_bucket_exist(self, bucket_name):
        try:
            oss_client = self.get_oss_client(bucket_name)
            oss_client.get_bucket_info()
        except NoSuchBucket:
            return False
        except Exception as excp:
            logger.error(f"UnexpectedError: {excp}")
            raise excp
        return True

    def upload_to_oss(self, src, bucket_name, dest):
        try:
            logger.info(f"Uploading {src} to bucket {bucket_name} as {dest}")
            oss_client = self.get_oss_client(bucket_name)
            oss_client.put_object_from_file(dest, src)
        except Exception as excp:
            logger.error(f"UnexpectedError: {excp}")
            raise excp

    def download_from_oss(self, src, bucket_name, dest):
        try:
            logger.info(
                f"Downloading {src} from {bucket_name} to local system as {dest}")
            oss_client = self.get_oss_client(bucket_name)
            oss_client.get_object_to_file(src, dest)
        except Exception as excp:
            logger.error(f"UnexpectedError: {excp}")
            raise excp

    def get_scaling_groups(self, project_name):
        try:
            _scaling_groups = []
            req = DescribeScalingGroupsRequest()
            req.set_PageSize(50)
            response = self._send_request(req)
            for i in response['ScalingGroups']['ScalingGroup']:
                if project_name in i['ScalingGroupName']:
                    _scaling_groups.append(i['ScalingGroupId'])
            return _scaling_groups
        except Exception as excp:
            logger.error(f"UnexpectedError: {excp}")
            raise excp

    def get_scaling_group_config(self, scaling_group_id):
        try:
            req = DescribeScalingConfigurationsRequest()
            req.set_PageSize(50)
            req.set_ScalingGroupId(scaling_group_id)
            return self._send_request(req)
        except Exception as excp:
            logger.error(f"UnexpectedError: {excp}")
            raise excp

    def update_image(self, image_id, project_name):
        updated_asg_list = []
        try:
            scaling_groups = self.get_scaling_groups(project_name)
            for sg in scaling_groups:
                asg_tags = self.get_asg_tags(sg)
                if asg_tags['SubType'] in ['MP', 'Router']:
                    sg_config = self.get_scaling_group_config(sg)
                    req = ModifyScalingConfigurationRequest()
                    sg_config_id = sg_config['ScalingConfigurations']['ScalingConfiguration'][0]['ScalingConfigurationId']
                    req.set_ScalingConfigurationId(sg_config_id)
                    req.set_ImageId(image_id)
                    res = self._send_request(req)
                    sg_name = sg_config['ScalingConfigurations']['ScalingConfiguration'][0]['ScalingConfigurationName']
                    updated_asg_list.append(sg_name)
            return updated_asg_list
        except Exception as excp:
            logger.error(f"UnexpectedError: {excp}")
            raise excp

    def get_attached_policy(self, role_name):
        request = ListPoliciesForRoleRequest()
        request.set_RoleName(role_name)
        response = self._send_request(request)
        policy = response['Policies']['Policy'][0]
        return policy

    def get_policy_document(self, policy):
        policy_name = policy['PolicyName']
        policy_type = policy['PolicyType']
        request = GetPolicyRequest()
        request.set_PolicyName(policy_name)
        request.set_PolicyType(policy_type)
        response = self._send_request(request)
        policy_doc = json.loads(response['DefaultPolicyVersion']['PolicyDocument'])
        return policy_doc

    def take_volume_snapshot(self,instance_ip, project_name):
        try:
            instance_id = self.get_instance_id_from_ip(instance_ip, project_name)
            snapshot_name_suffix = datetime.datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
            request = DescribeDisksRequest()
            request.set_InstanceId(instance_id)
            request.set_DiskType('data')
            response = self._send_request(request)
            disks = response['Disks']['Disk']
            snapshot_ids = []
            disk_ids = [i['DiskId'] for i in disks]
            for id in disk_ids:
                snapshot_name = f"{id}-{snapshot_name_suffix}"
                request = CreateSnapshotRequest()
                request.set_DiskId(id)
                request.set_SnapshotName(snapshot_name)
                response = self._send_request(request)

                snapshot_id = response['SnapshotId']
                while True:
                    time.sleep(10)
                    describe_request = DescribeSnapshotsRequest()
                    describe_request.set_SnapshotIds([snapshot_id])
                    describe_response = self._send_request(describe_request)
                    snapshots = describe_response['Snapshots']['Snapshot']

                    if snapshots[0]['Status'] == 'accomplished':
                        snapshot_ids.append(response['SnapshotId'])
                        break

            return snapshot_ids

        except Exception as excp:
            logger.error(f"UnexpectedError: {excp}")
            raise excp
