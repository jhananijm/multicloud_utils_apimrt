import os
import json
import unittest
from unittest import mock
from unittest.mock import patch
from apimrt.clouds.alibaba.alibaba_utils import AliBabaUtil
from apimrt.tests.clouds.alibaba.common_utils import get_mock_json 

class TestAliBabaUtil(unittest.TestCase):
    def setUp(self) -> None:
        self.access_key_id = "access_key_id"
        self.access_key_secret = "access_key_secret"
        self.security_token = "security_token"
        self.region_id = "region_id"

        ali_util = AliBabaUtil(self.region_id,self.access_key_id,self.access_key_secret,self.security_token)
        self.assertEqual(ali_util.region_id, self.region_id)
        self.assertEqual(ali_util.access_key_id, self.access_key_id)
        self.assertEqual(ali_util.access_key_secret, self.access_key_secret)
        self.assertEqual(ali_util.security_token, self.security_token)

    @mock.patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil._send_request')
    def test_get_secrets(self, mock_secrets):
        mock_secrets.return_value = get_mock_json('metadata')
        ali_util = AliBabaUtil(region_id='region_id', access_key_id='access_key_id', 
                               access_key_secret='access_key_secret',security_token='security_token')
        resp = ali_util.get_secrets(secret_name='secret_name')
        self.assertEqual(json.loads(mock_secrets.return_value['SecretData']), resp)
        mock_secrets.return_value = get_mock_json('metadata')['SecretData']
        resp = ali_util.get_secrets(secret_name='secret_name')

    @mock.patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil._send_request')
    def test_get_instance_private_ip(self, mock_ip):
        mock_ip.return_value = get_mock_json('instance')
        ali_util = AliBabaUtil(region_id='region_id', access_key_id='access_key_id', 
                               access_key_secret='access_key_secret',security_token='security_token')
        resp = ali_util.get_instance_private_ip(instance_id='instance_id')
        self.assertEqual('192.168.12.139', resp)
        mock_ip.return_value = get_mock_json('instance_fail')['Instance1']
        resp = ali_util.get_instance_private_ip(instance_id='instance_id')
        mock_ip.return_value = get_mock_json('instance_fail')['Instance2']
        resp = ali_util.get_instance_private_ip(instance_id='instance_id')

    @mock.patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil._send_request')
    def test_get_instance_name_from_id(self,mock_id):
        mock_id.return_value = get_mock_json('instance')
        ali_util = AliBabaUtil(region_id='region_id', access_key_id='access_key_id', 
                               access_key_secret='access_key_secret',security_token='security_token')
        resp = ali_util.get_instance_name_from_id(instance_id='instance_id')
        self.assertEqual('cpabs-10516-custom-router', resp)
        mock_id.return_value = get_mock_json('instance_fail')['Instance1']
        resp = ali_util.get_instance_name_from_id(instance_id='instance_id')
        mock_id.return_value = get_mock_json('instance_fail')['Instance2']
        resp = ali_util.get_instance_name_from_id(instance_id='instance_id')

    @mock.patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil._send_request')
    def test_get_instance_id_from_ip(self,mock_ip):
        mock_ip.return_value = get_mock_json('instance')
        mock_ip.get.side_effect = Exception("UnexpectedError")
        ali_util = AliBabaUtil(region_id='region_id', access_key_id='access_key_id', 
                               access_key_secret='access_key_secret',security_token='security_token')
        resp = ali_util.get_instance_id_from_ip(instance_ip='instance_ip', project_name='project_name')
        self.assertEqual('i-uf69ub1qaf2lawpt6q53', resp)
        mock_ip.return_value = get_mock_json('instance_fail')['Instance1']
        resp = ali_util.get_instance_id_from_ip(instance_ip='instance_ip', project_name='project_name')
        mock_ip.return_value = get_mock_json('instance_fail')['Instance2']
        resp = ali_util.get_instance_id_from_ip(instance_ip='instance_ip', project_name='project_name')

    @mock.patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil._send_request')
    def test_get_instance_tags(self, mock_tags):
        mock_tags.return_value = get_mock_json('instance')
        ali_util = AliBabaUtil(region_id='region_id', access_key_id='access_key_id', 
                               access_key_secret='access_key_secret',security_token='security_token')
        resp = ali_util.get_instance_tags(instance_id='instance_id')
        self.assertEqual('runtime', resp['Type'])
        mock_tags.return_value = get_mock_json('instance_fail')['Instance1']
        resp = ali_util.get_instance_tags(instance_id='instance_id')
        mock_tags.return_value = get_mock_json('instance_fail')['Instance3']
        resp = ali_util.get_instance_tags(instance_id='instance_id')

    @mock.patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil._send_request')
    def test_complete_lifecycle_action(self, mock_ls):
        mock_ls.return_value = "True"
        ali_util = AliBabaUtil(region_id='region_id', access_key_id='access_key_id', 
                               access_key_secret='access_key_secret',security_token='security_token')
        resp = ali_util.complete_lifecycle_action(
            LifecycleHookId='LifecycleHookId', LifecycleActionToken='LifecycleActionToken')
        self.assertEqual(True, resp)

        mock_ls.return_value = None
        resp = ali_util.complete_lifecycle_action(
            LifecycleHookId='LifecycleHookId', LifecycleActionToken='LifecycleActionToken')
        self.assertEqual(False, resp)

    @mock.patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil._send_request')
    def test_get_asg_id_from_asg_name(self, mock_data):
        mock_data.return_value = get_mock_json('scaling')
        ali_util = AliBabaUtil(region_id='region_id', access_key_id='access_key_id', 
                               access_key_secret='access_key_secret',security_token='security_token')
        resp = ali_util.get_asg_id_from_asg_name(asg_name='asg_name')
        self.assertEqual('asg-uf6h4xevumiy10rtt7da', resp)
        try:
            mock_data.return_value = get_mock_json('scaling_fail')[
                'ScalingGroups1']
            resp = ali_util.get_asg_id_from_asg_name(asg_name='asg_name')
        except ValueError:
            pass
        try:
            mock_data.return_value = get_mock_json('scaling_fail')[
                'ScalingGroups2']
            resp = ali_util.get_asg_id_from_asg_name(asg_name='asg_name')
        except ValueError:
            pass

    @mock.patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil._send_request')
    def test_get_asg_name_from_asg_id(self, mock_data):
        mock_data.return_value = get_mock_json('scaling')
        ali_util = AliBabaUtil(region_id='region_id', access_key_id='access_key_id', 
                               access_key_secret='access_key_secret',security_token='security_token')

        resp = ali_util.get_asg_name_from_asg_id(asg_id='asg_id')
        self.assertEqual('cpabs-10516-ess-custom-mp', resp)
        try:
            mock_data.return_value = get_mock_json('scaling_fail')[
                'ScalingGroups1']
            resp = ali_util.get_asg_name_from_asg_id(asg_id='asg_id')
        except ValueError:
            pass
        try:
            mock_data.return_value = get_mock_json('scaling_fail')[
                'ScalingGroups2']
            resp = ali_util.get_asg_name_from_asg_id(asg_id='asg_id')
        except ValueError:
            pass

    @mock.patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil._send_request')
    def test_get_instances_id_from_asg(self, mock_data):
        mock_data.return_value = get_mock_json('scaling_instance')
        ali_util = AliBabaUtil(region_id='region_id', access_key_id='access_key_id', 
                               access_key_secret='access_key_secret',security_token='security_token')
        resp = ali_util.get_instances_id_from_asg(asg_id='asg_id')
        self.assertEqual(['i-uf62y8khhbk9ycy6w401'], resp)

    @mock.patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil._send_request')
    def test_get_asg_tags(self, mock_data):
        mock_data.return_value = get_mock_json('asg_tags')
        ali_util = AliBabaUtil(region_id='region_id', access_key_id='access_key_id', 
                               access_key_secret='access_key_secret',security_token='security_token')
        resp = ali_util.get_asg_tags(asg_id='asg_id')
        self.assertEqual('MP', resp['SubType'])

    @mock.patch('aliyunsdkcore.client.AcsClient')
    def test_get_client(self, mock_data):
        mock_data.return_value = "client"
        ali_util = AliBabaUtil(region_id='region_id', access_key_id='access_key_id', 
                               access_key_secret='access_key_secret',security_token='security_token')
        resp = ali_util.get_client

    def test_get_oss_client(self):
        with mock.patch('oss2.Bucket') as mock_data:
            mock_data.return_value = "client"
            ali_util = AliBabaUtil(region_id='region_id', access_key_id='access_key_id', 
                               access_key_secret='access_key_secret',security_token='security_token')
            resp = ali_util.get_oss_client(bucket_name='bucket_name')

    @mock.patch('alibabacloud_credentials.models.Config')
    def test_get_sts_creds(self, mock_config):
        mock_config.return_value = "client"
        with mock.patch('alibabacloud_credentials.client.Client.get_credential') as mock_data:
            mock_data_obj = mock.Mock()
            mock_data_obj.get_access_key_id.return_value = "key_id"
            mock_data_obj.get_access_key_secret.return_value = "key"
            mock_data_obj.get_security_token.return_value = "token"
            mock_data.return_value = mock_data_obj
            ali_util = AliBabaUtil(region_id='region_id', access_key_id='access_key_id', 
                               access_key_secret='access_key_secret',security_token='security_token')
            resp1, resp2, resp3 = ali_util.get_sts_creds(role_name='role_name')
            self.assertEqual(resp1, 'key_id', "Should be key_id")
            self.assertEqual(resp2, 'key', "Should be key")
            self.assertEqual(resp3, 'token', "Should be token")

    @mock.patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil.get_client')
    def test__send_request(self, mock_data):
        mock_data.return_value = "Test"
        with mock.patch('json.loads') as mock_json:
            mock_json.return_value = {"Test": "Test"}
            ali_util = AliBabaUtil(region_id='region_id', access_key_id='access_key_id', 
                               access_key_secret='access_key_secret',security_token='security_token')
            my_mock_response = mock.Mock(status_code=200)
            my_mock_response.json = {"request": "test"}
            resp = ali_util._send_request(request=my_mock_response)
            self.assertEqual(resp['Test'], 'Test')

    @mock.patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil.get_oss_client')
    def test_does_bucket_exist(self, mock_data):
        mock_data_obj = mock.Mock()
        mock_data_obj.get_bucket_info.return_value = "key_id"
        mock_data.return_value = mock_data_obj
        ali_util = AliBabaUtil(region_id='region_id', access_key_id='access_key_id', 
                               access_key_secret='access_key_secret',security_token='security_token')
        resp = ali_util.does_bucket_exist(bucket_name='example')
        self.assertEqual(resp, True)

    @mock.patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil.get_oss_client')
    def test_upload_to_oss(self, mock_data):
        mock_data_obj = mock.Mock()
        mock_data_obj.put_object_from_file.return_value = "key_id"
        mock_data.return_value = mock_data_obj
        ali_util = AliBabaUtil(region_id='region_id', access_key_id='access_key_id', 
                               access_key_secret='access_key_secret',security_token='security_token')
        resp = ali_util.upload_to_oss(
            src='example', bucket_name='example', dest='example')

    @mock.patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil.get_oss_client')
    def test_download_from_oss(self, mock_data):
        mock_data_obj = mock.Mock()
        mock_data_obj.get_object_to_file.return_value = "key_id"
        mock_data.return_value = mock_data_obj
        ali_util = AliBabaUtil(region_id='region_id', access_key_id='access_key_id', 
                               access_key_secret='access_key_secret',security_token='security_token')
        resp = ali_util.download_from_oss(
            src='example', bucket_name='example', dest='example')
    
    @mock.patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil._send_request')
    def test_get_scaling_groups(self, mock_data):
        mock_data.return_value = get_mock_json('scaling')
        scaling_group = mock_data.return_value['ScalingGroups']['ScalingGroup']
        project_name = 'cpabs-10516'
        ali_util = AliBabaUtil(region_id='region_id', access_key_id='access_key_id', 
                               access_key_secret='access_key_secret',security_token='security_token')
        resp = ali_util.get_scaling_groups(project_name=project_name)
        self.assertEqual(['asg-uf6h4xevumiy10rtt7da'], resp)

    @mock.patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil._send_request')
    def test_get_scaling_group_config(self, mock_data):
        mock_data.return_value = get_mock_json('scaling')
        ali_util = AliBabaUtil(region_id='region_id', access_key_id='access_key_id', 
                               access_key_secret='access_key_secret',security_token='security_token')
        resp = ali_util.get_scaling_group_config(scaling_group_id='scaling_group_id')  

    @mock.patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil._send_request')
    def test_get_attached_policy(self, mock_data):
        mock_data.return_value = get_mock_json('attached_policy')
        ali_util = AliBabaUtil(region_id='region_id', access_key_id='access_key_id', 
                               access_key_secret='access_key_secret',security_token='security_token')
        resp = ali_util.get_attached_policy(role_name='role_name')
        self.assertEqual(resp,mock_data.return_value['Policies']['Policy'][0])

    @mock.patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil._send_request')
    def test_get_policy_document(self, mock_send_request):
        mock_response = {'DefaultPolicyVersion': {'PolicyDocument': '{"key": "value"}'}}
        mock_send_request.return_value = mock_response
        ali_util = AliBabaUtil(region_id='region_id',access_key_id='access_key_id',
                                access_key_secret='access_key_secret',security_token='security_token')
        policy = {'PolicyName': 'policy_name','PolicyType': 'policy_type'}
        policy_doc = ali_util.get_policy_document(policy)
        self.assertEqual(policy_doc, {'key': 'value'})

    @mock.patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil.get_scaling_groups')
    @mock.patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil.get_asg_tags')
    @mock.patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil.get_scaling_group_config')
    @mock.patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil._send_request')
    def test_update_image(self, mock_send_request, mock_get_scaling_group_config, mock_get_asg_tags, mock_get_scaling_groups):
        ali_util = AliBabaUtil(region_id='region_id',access_key_id='access_key_id',
                                access_key_secret='access_key_secret',security_token='security_token')
        mock_get_scaling_groups.return_value = ['scaling_group_1', 'scaling_group_2']
        mock_get_asg_tags.side_effect = [{'SubType': 'MP'}, {'SubType': 'SomeOtherType'}]
        mock_get_scaling_group_config.side_effect = get_mock_json('scaling_group')
        result = ali_util.update_image(image_id='new_image_id', project_name='my_project')
        expected_asg_list = ['config_name_1']
        self.assertEqual(result, expected_asg_list)
    
    @patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil.get_instance_id_from_ip')
    @patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil._send_request')
    @patch('apimrt.clouds.alibaba.alibaba_utils.time.sleep')
    def test_take_volume_snapshot(self, mock_sleep, mock_send_request, mock_get_instance_id_from_ip):
        ali_util = AliBabaUtil(region_id='region_id',access_key_id='access_key_id',
                                access_key_secret='access_key_secret',security_token='security_token')
        mock_get_instance_id_from_ip.return_value = 'mock_instance_id'
        mock_send_request.side_effect = get_mock_json('snapshot')
        result = ali_util.take_volume_snapshot(instance_ip='mock_ip', project_name='my_project')