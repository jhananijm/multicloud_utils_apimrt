import unittest
from unittest import mock
from apimrt.clouds.gcp.gcp_meta import Gcp

class GcpMetaTestCase(unittest.TestCase):
    def setUp(self):
        self.gcp_meta = Gcp()
        
    @mock.patch('requests.get')
    def test_get_project_name(self, mock_get):
        my_mock_response = mock.Mock(status_code=200)
        my_mock_response.text = 'example'
        mock_get.return_value = my_mock_response
        resp = self.gcp_meta.get_project_name()
        self.assertEqual(
            'example', resp)
        
    @mock.patch('requests.get')
    def test_get_service_account(self, mock_get):
        my_mock_response = mock.Mock(status_code=200)
        my_mock_response.text = 'example1'
        mock_get.return_value = my_mock_response
        resp = self.gcp_meta.get_service_account()
        self.assertEqual(
            ['example1'], resp)
        
    @mock.patch('requests.get')
    def test_get_access_token(self, mock_get):
        with mock.patch('apimrt.clouds.gcp.gcp_meta.Gcp.get_service_account') as mock_srv_acc:
            mock_srv_acc.return_value = ['example']
            my_mock_response = mock.Mock(status_code=200)
            my_mock_response.text = '{"access_token":"example1"}'
            mock_get.return_value = my_mock_response
            resp = self.gcp_meta.get_access_token()
            self.assertEqual(
                'example1', resp)
            
    @mock.patch('requests.get')
    def test_get_global_project_id(self, mock_get):
        my_mock_response = mock.Mock(status_code=200)
        my_mock_response.text = 'example1'
        mock_get.return_value = my_mock_response
        resp = self.gcp_meta.get_global_project_id()
        self.assertEqual(
            'example1', resp)
        
    def test_get_secrets(self):
        with mock.patch('apimrt.clouds.gcp.gcp_meta.Gcp.get_global_project_id') as mock_id:
            mock_id.return_value = 'example'
            with mock.patch('apimrt.clouds.gcp.gcp_meta.Gcp.get_project_name') as mock_prj:
                mock_prj.return_value = 'example'
                with mock.patch('apimrt.clouds.gcp.gcp_utils.GcpUtil.get_secrets') as mock_secrets:
                    mock_secrets.return_value = {'example':'test'}
                    resp = self.gcp_meta.get_secrets()
                    self.assertEqual(
                        'test', resp['example'])
                    
    def test_get_project_secret_name(self):
        with mock.patch('apimrt.clouds.gcp.gcp_meta.Gcp.get_project_name') as mock_prj:
            mock_prj.return_value = 'example'
            resp = self.gcp_meta.get_project_secret_name()
            self.assertEqual('example-secrets', resp)
            
    def test_take_volume_snapshot(self):
        with mock.patch('apimrt.clouds.gcp.gcp_meta.Gcp.get_global_project_id') as mock_id:
            mock_id.return_value = 'example'
            with mock.patch('apimrt.clouds.gcp.gcp_meta.Gcp.get_project_name') as mock_prj:
                mock_prj.return_value = 'example'
                with mock.patch('apimrt.clouds.gcp.gcp_utils.GcpUtil.take_volume_snapshot') as mock_data:
                    mock_data.return_value = 'example'
                    resp = self.gcp_meta.take_volume_snapshot('example')
                    self.assertEqual(
                        'example', resp)
                    
    def test_get_instance_name(self):
        with mock.patch('apimrt.clouds.gcp.gcp_meta.Gcp.get_global_project_id') as mock_id:
            mock_id.return_value = 'example'
            with mock.patch('apimrt.clouds.gcp.gcp_utils.GcpUtil.get_instance_name') as mock_data:
                mock_data.return_value = 'example'
                resp = self.gcp_meta.get_instance_name('example','example')
                self.assertEqual(
                    'example', resp)
                
    def test_get_project_instance_name(self):
        with mock.patch('apimrt.clouds.gcp.gcp_meta.Gcp.get_global_project_id') as mock_id:
            mock_id.return_value = 'example'
            with mock.patch('apimrt.clouds.gcp.gcp_meta.Gcp.get_project_name') as mock_prj:
                mock_prj.return_value = 'example'
                with mock.patch('apimrt.clouds.gcp.gcp_utils.GcpUtil.get_instance_name') as mock_data:
                    mock_data.return_value = 'example'
                    resp = self.gcp_meta.get_project_instance_name('example')
                    self.assertEqual(
                        'example', resp)
            
    def test_get_instance_tags(self):
        with mock.patch('apimrt.clouds.gcp.gcp_meta.Gcp.get_global_project_id') as mock_id:
            mock_id.return_value = 'example'
            with mock.patch('apimrt.clouds.gcp.gcp_meta.Gcp.get_project_name') as mock_prj:
                mock_prj.return_value = 'example'
                with mock.patch('apimrt.clouds.gcp.gcp_utils.GcpUtil.get_instance_tags') as mock_data:
                    mock_data.return_value = 'example'
                    resp = self.gcp_meta.get_instance_tags('example')
                    self.assertEqual(
                        'example', resp)
            
        