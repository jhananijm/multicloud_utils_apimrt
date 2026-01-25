from apimrt.clouds.alibaba.alibaba_meta import AlibabaMeta
import unittest
from unittest.mock import patch, MagicMock
from apimrt.clouds.alibaba.alibaba_utils import AliBabaUtil
from apimrt.tests.clouds.alibaba.common_utils import get_mock_json

class TestAlibabaMeta(unittest.TestCase):

    @patch('apimrt.clouds.alibaba.alibaba_meta.requests.get')
    def test_init(self, mock_get):
        mock_get.return_value.json.return_value = {"example_key": "example_value"}
        mock_get.return_value.status_code = 200
        alibaba_meta = AlibabaMeta()
        self.assertEqual(alibaba_meta._METADATA, {"example_key": "example_value"})

    @patch('apimrt.clouds.alibaba.alibaba_meta.requests.get')
    def test_get_region_id(self, mock_get):
        mock_get.return_value.json.return_value = {"region-id": "example_region_id"}
        alibaba_meta = AlibabaMeta()
        region_id = alibaba_meta.get_region_id()
        self.assertEqual(region_id, "example_region_id")

    @patch('apimrt.clouds.alibaba.alibaba_meta.requests.get')
    def test_get_sts_creds(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"AccessKeyId": "access_key","AccessKeySecret": "access_secret",
            "SecurityToken": "security_token"}
        mock_get.return_value = mock_resp
        alibaba_meta = AlibabaMeta()
        access_key_id, access_key_secret, security_token = alibaba_meta.get_sts_creds()
        self.assertEqual(access_key_id, "access_key")
        self.assertEqual(access_key_secret, "access_secret")
        self.assertEqual(security_token, "security_token")

    @patch('apimrt.clouds.alibaba.alibaba_meta.requests.get')
    @patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil')
    def test_get_ali_util(self, mock_get, mock_util):
        alibaba_meta = AlibabaMeta()
        alibaba_meta.get_sts_creds = MagicMock(return_value=("access-key-id", "access-key-secret", "security-token"))
        alibaba_meta.get_region_id = MagicMock(return_value="us-west-1")
        ali_util = alibaba_meta.get_ali_util()

    @patch('apimrt.clouds.alibaba.alibaba_meta.requests.get')
    @patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil.get_instance_tags')
    def test_get_project_name(self, mock_get_instance_tags, mock_get):
        mock_get.return_value = MagicMock(json=lambda: {'region-id': 'us-west-1', 'instance-id': '12345'})
        mock_get_instance_tags.return_value = {'Project': 'MyProject'}
        alibaba_meta = AlibabaMeta()
        ali_util_mock = MagicMock(spec=AliBabaUtil)
        ali_util_mock.get_instance_tags.return_value = {'Project': 'MyProject'}
        with patch.object(alibaba_meta, 'get_ali_util', return_value=ali_util_mock):
            project_name = alibaba_meta.get_project_name()
        self.assertEqual(project_name, 'MyProject')
    
    @patch('apimrt.clouds.alibaba.alibaba_meta.requests.get')
    @patch('apimrt.clouds.alibaba.alibaba_utils.AliBabaUtil.get_secrets')
    def test_get_secrets(self, mock_get, mock_get_secrets):
        mock_get.return_value = MagicMock(json=lambda: {'region-id': 'us-west-1', 'instance-id': '12345'})
        alibaba_meta = AlibabaMeta()
        ali_util_mock = MagicMock(spec=AliBabaUtil)
        alibaba_meta.get_project_name = MagicMock(return_value ="project_name")
        ali_util_mock.get_secrets.return_value = {'SecretKey': 'abc123'}
        with patch.object(alibaba_meta, 'get_ali_util', return_value=ali_util_mock):
            secrets = alibaba_meta.get_secrets()
        self.assertEqual(secrets, {'SecretKey': 'abc123'})
    
    @patch('apimrt.clouds.alibaba.alibaba_meta.requests.get')
    def test_get_scaling_groups(self, mock_get):
        mock_get.return_value = MagicMock(json=lambda: {'region-id': 'us-west-1', 'instance-id': '12345'})
        alibaba_meta = AlibabaMeta()
        ali_util_mock = MagicMock(spec=AliBabaUtil)
        ali_util_mock.get_scaling_groups.return_value = ['asg_id_1', 'asg_id_2']
        ali_util_mock.get_asg_name_from_asg_id.side_effect = lambda asg_id: f'ASG-{asg_id}'
        with patch.object(alibaba_meta, 'get_ali_util', return_value=ali_util_mock):
            scaling_groups = alibaba_meta.get_scaling_groups()
        self.assertEqual(scaling_groups, ['ASG-asg_id_1', 'ASG-asg_id_2'])

    @patch('apimrt.clouds.alibaba.alibaba_meta.requests.get')
    def test_update_image(self, mock_get):
        mock_get.return_value = MagicMock(json=lambda: {'region-id': 'us-west-1', 'instance-id': '12345'})
        alibaba_meta = AlibabaMeta()
        ali_util_mock = MagicMock(spec=AliBabaUtil)
        ali_util_mock.update_image.return_value = 'Image updated'
        with patch.object(alibaba_meta, 'get_ali_util', return_value=ali_util_mock):
            result = alibaba_meta.update_image('image123')
        self.assertEqual(result, 'Image updated')

    @patch('apimrt.clouds.alibaba.alibaba_meta.requests.get')
    def test_take_volume_snapshot(self, mock_get):
        mock_get.return_value = MagicMock(json=lambda: {'region-id': 'us-west-1', 'instance-id': '12345'})
        alibaba_meta = AlibabaMeta()
        ali_util_mock = MagicMock(spec=AliBabaUtil)
        ali_util_mock.take_volume_snapshot.return_value = 'Snapshot taken'
        with patch.object(alibaba_meta, 'get_ali_util', return_value=ali_util_mock):
            result = alibaba_meta.take_volume_snapshot('192.168.0.1')
        self.assertEqual(result, 'Snapshot taken')

    @patch('apimrt.clouds.alibaba.alibaba_meta.requests.get')
    def test_get_instance_name(self, mock_get):
        mock_get.return_value = MagicMock(json=lambda: {'region-id': 'us-west-1', 'instance-id': '12345'})
        alibaba_meta = AlibabaMeta()
        ali_util_mock = MagicMock(spec=AliBabaUtil)
        ali_util_mock.get_instance_id_from_ip.return_value = 'i-12345678'
        ali_util_mock.get_instance_name_from_id.return_value = 'instance_name'
        with patch.object(alibaba_meta, 'get_ali_util', return_value=ali_util_mock):
            result = alibaba_meta.get_instance_name('192.168.0.1', 'project_name')
        self.assertEqual(result, 'instance_name')
    
    @patch('apimrt.clouds.alibaba.alibaba_meta.requests.get')
    def test_get_project_instance_name(self, mock_get):
        mock_get.return_value = MagicMock(json=lambda: {'region-id': 'us-west-1', 'instance-id': '12345'})
        alibaba_meta = AlibabaMeta()
        ali_util_mock = MagicMock(spec=AliBabaUtil)
        ali_util_mock.get_instance_id_from_ip.return_value = 'i-12345678'
        ali_util_mock.get_instance_name_from_id.return_value = 'instance_name'
        with patch.object(alibaba_meta, 'get_ali_util', return_value=ali_util_mock):
            result = alibaba_meta.get_project_instance_name('192.168.0.1')
        self.assertEqual(result, 'instance_name')

    @patch('apimrt.clouds.alibaba.alibaba_meta.requests.get')
    def test_get_instance_tags(self, mock_get):
        mock_get.return_value = MagicMock(json=lambda: {'region-id': 'us-west-1', 'instance-id': '12345'})
        alibaba_meta = AlibabaMeta()
        ali_util_mock = MagicMock(spec=AliBabaUtil)
        ali_util_mock.get_instance_id_from_ip.return_value = 'i-12345678'
        ali_util_mock.get_instance_tags.return_value = {'Project': 'project_name'}
        with patch.object(alibaba_meta, 'get_ali_util', return_value=ali_util_mock):
            result = alibaba_meta.get_instance_tags('192.168.0.1')
        self.assertEqual(result, {'Project': 'project_name'})

    @patch('apimrt.clouds.alibaba.alibaba_meta.requests.get')
    def test_get_role_name(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.text = 'role_name'
        alibaba_meta = AlibabaMeta()
        result = alibaba_meta.get_role_name()
        self.assertEqual(result, 'role_name')

    @patch('apimrt.clouds.alibaba.alibaba_meta.requests.get')
    def test_get_available_permissions(self, mock_get):
        alibaba_meta = AlibabaMeta()
        ali_util_mock = MagicMock(spec=AliBabaUtil)
        ali_util_mock.get_attached_policy.return_value = "policy_name"
        ali_util_mock.get_policy_document.return_value = get_mock_json('policy_document')
        with patch.object(alibaba_meta, 'get_ali_util', return_value=ali_util_mock):
            result = alibaba_meta.get_available_permissions()
        self.assertEqual(result, ["action1", "action2", "action4"])

    @patch('apimrt.clouds.alibaba.alibaba_meta.requests.get')
    def test_get_project_secret_name(self, mock_get):
        alibaba_meta = AlibabaMeta()
        project_name = "project_name"
        alibaba_meta.get_project_name = MagicMock(return_value=project_name)
        result = alibaba_meta.get_project_secret_name()
        expected_name = f"{project_name}-secret"
        self.assertEqual(result, expected_name)