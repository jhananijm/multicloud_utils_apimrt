import unittest
from unittest import mock
from unittest.mock import MagicMock, patch

from apimrt.clouds.gcp.gcp_utils import GcpUtil


class GcpUtilTestCase(unittest.TestCase):
    def setUp(self):
        self.gcp_util = GcpUtil(project_id="test-project")

    @patch('apimrt.clouds.gcp.gcp_utils.compute_v1.InstancesClient')
    def test_get_instance_data(self, mock_instances_client):
        mock_instances_client.return_value.aggregated_list.return_value = [
            ('zone1', MagicMock(instances=
                [MagicMock(metadata=MagicMock(items=[MagicMock(key='project', value='project1')]),
                          network_interfaces=[MagicMock(network_i_p='192.168.0.1')])]
            )),
            ('zone2', MagicMock(instances=
                [MagicMock(metadata=MagicMock(items=[MagicMock(key='project', value='project2')]),
                          network_interfaces=[MagicMock(network_i_p='192.168.0.2')])]
            )),
        ]
        

        instance_data, zone = self.gcp_util.get_instance_data('192.168.0.1', 'project1')
        self.assertIsNotNone(instance_data)
        self.assertEqual(zone, 'zone1')

        instance_data, zone = self.gcp_util.get_instance_data('192.168.0.2', 'project2')
        self.assertIsNotNone(instance_data)
        self.assertEqual(zone, 'zone2')

        instance_data, zone = self.gcp_util.get_instance_data('192.168.0.3', 'project3')
        self.assertIsNone(instance_data)
        self.assertIsNone(zone)

    @patch('apimrt.clouds.gcp.gcp_utils.GcpUtil.get_instance_data')
    def test_get_instance_name(self, mock_instance_data):
        instance_data = MagicMock()
        instance_data.name = "instance1"
        mock_instance_data.return_value = (instance_data, 'zone')

        instance_name = self.gcp_util.get_instance_name('192.168.0.1', 'project1')
        self.assertEqual(instance_name, instance_data.name)

        mock_instance_data.return_value = (None, None)

        instance_name = self.gcp_util.get_instance_name('192.168.0.3', 'project3')
        self.assertIsNone(instance_name)

    @patch('apimrt.clouds.gcp.gcp_utils.compute_v1.InstancesClient')
    def test_get_instance_tags(self, mock_instances_client):
        mock_instances_client.return_value.aggregated_list.return_value = [
            ('zone1', MagicMock(instances=
                [MagicMock(metadata=MagicMock(items=[MagicMock(key='project', value='project1'), MagicMock(key='tag1', value='value1'),
                    MagicMock(key='tag2', value='value2')]),
                          network_interfaces=[MagicMock(network_i_p='192.168.0.1')])]
            )),
            ('zone2', MagicMock(instances=
                [MagicMock(metadata=MagicMock(items=[MagicMock(key='project', value='project2'),MagicMock(key='tag1', value='value1'),
                    MagicMock(key='tag2', value='value2')]),
                          network_interfaces=[MagicMock(network_i_p='192.168.0.2')])]
            )),
        ]

        tags = self.gcp_util.get_instance_tags('192.168.0.1', 'project1')
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags['tag1'], 'value1')
        self.assertEqual(tags['tag2'], 'value2')

        tags = self.gcp_util.get_instance_tags('192.168.0.2', 'project2')
        self.assertEqual(len(tags), 3)
        self.assertEqual(tags['tag1'], 'value1')
        self.assertEqual(tags['tag2'], 'value2')

        tags = self.gcp_util.get_instance_tags('192.168.0.3', 'project3')
        self.assertIsNone(tags)
        
    @patch('apimrt.clouds.gcp.gcp_utils.secretmanager.SecretManagerServiceClient')
    def test_get_secrets(self, mock_client):
        mocked_secret_value = '{"key": "value"}'
        mock_secret_manager_client = mock_client.return_value
        mock_secret_manager_client.access_secret_version.return_value.payload.data.decode.return_value = mocked_secret_value
        result = self.gcp_util.get_secrets("your_secret_id")
        self.assertEqual(result, {"key": "value"})
        
    @patch('apimrt.clouds.gcp.gcp_utils.compute_v1.InstancesClient')
    def test_list_attached_volumes(self, mock_instances_client):
        mock_instances_client.return_value.get.return_value = MagicMock(
            disks=[
                MagicMock(source='/projects/test-project/zones/zone1/disks/disk1', boot=False),
                MagicMock(source='/projects/test-project/zones/zone1/disks/disk2', boot=True),
                MagicMock(source='/projects/test-project/zones/zone1/disks/disk3', boot=False),
            ]
        )

        volumes = self.gcp_util.list_attached_volumes('zone1', 'instance1')
        self.assertEqual(len(volumes), 2)
        self.assertIn('disk1', volumes)
        self.assertIn('disk3', volumes)

    def test_create_volume_snapshot(self):
        with mock.patch('apimrt.clouds.gcp.gcp_utils.compute_v1.DisksClient') as mock_disk_client:
            mock_disk_client.get.return_value = "disk1"
            with mock.patch('apimrt.clouds.gcp.gcp_utils.compute_v1.RegionDisksClient') as mock_rdisk_client:
                mock_rdisk_client.get.return_value = "disk1"
                with mock.patch('apimrt.clouds.gcp.gcp_utils.compute_v1.Snapshot') as mock_snapshot:
                    mock_snapshot.return_value = MagicMock(source_disk='disk1', name='disk1', storage_locations='zone1')
                    with mock.patch('apimrt.clouds.gcp.gcp_utils.compute_v1.SnapshotsClient') as mock_snapshots_client:
                        mock_snapshots_client.return_value.insert.return_value = MagicMock(get='snapshot1')
                        mock_snapshots_client.return_value.get.return_value = MagicMock(get='snapshot1')
                        with mock.patch('apimrt.clouds.gcp.gcp_utils.GcpUtil.wait_for_extended_operation') as mock_ext_opr:
                            mock_ext_opr.return_value = True
                            snapshot = self.gcp_util.create_volume_snapshot(
                                project_id='test-project',
                                disk_name='disk1',
                                snapshot_name='snapshot1',
                                zone='zone1'
                            )

                            self.assertEqual(snapshot.get, 'snapshot1')
                            
                            snapshot = self.gcp_util.create_volume_snapshot(
                                project_id='test-project',
                                disk_name='disk1',
                                snapshot_name='snapshot1',
                                region='zone1',
                                location='zone1'
                            )
                            
                            self.assertEqual(snapshot.get, 'snapshot1')

    def test_take_volume_snapshot(self):
        with mock.patch('apimrt.clouds.gcp.gcp_utils.GcpUtil.get_instance_data') as mock_data:
            instance_data = MagicMock(name='instance_data')
            instance_data.name = 'instance1'
            zone = 'region/us-east1'
            mock_data.return_value = (instance_data, zone)
            with mock.patch('apimrt.clouds.gcp.gcp_utils.GcpUtil.list_attached_volumes') as mock_vol_list:
                mock_vol_list.return_value = ['vol1','vol2']
                with mock.patch('apimrt.clouds.gcp.gcp_utils.GcpUtil.create_volume_snapshot') as mock_snapshot_name:
                    snapshot_name = mock_snapshot_name.return_value
                    snapshot_name.name = "snapshot_name"
                    snapshots = self.gcp_util.take_volume_snapshot('192.168.0.1', 'project1')
                    self.assertEqual(snapshots[0], 'snapshot_name')
                    
    
    def test_wait_for_extended_operation_success(self):
        operation = MagicMock()
        operation.result = MagicMock(return_value="result")
        operation.error_code = None
        operation.warnings = None
        result = self.gcp_util.wait_for_extended_operation(operation)
        self.assertEqual(result, "result")
        
    def test_wait_for_extended_operation_warning(self):
        operation = MagicMock()
        operation.result = MagicMock(return_value="result")
        operation.error_code = None
        operation.warnings = [MagicMock(code='error_code', message='error_message')]
        self.gcp_util.wait_for_extended_operation(operation)

    def test_wait_for_extended_operation_error(self):
        operation = MagicMock()
        operation.result = MagicMock(return_value="result")
        operation.error_code = "error_code"
        operation.error_message = "error_message"
        operation.name = "operation_id"
        operation.exception = MagicMock(return_value=None)
        with self.assertRaises(RuntimeError):
            self.gcp_util.wait_for_extended_operation(operation)