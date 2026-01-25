# import unittest
# from unittest.mock import patch 
# from cloud_meta.cloud_register import CloudMetaRegister
# import yaml

# class TestCloudMetaRegister(unittest.TestCase):
#     def test_get_required_permissions(self):
#         cloud_reg = CloudMetaRegister()
#         expected_permissions = ["permission1", "permission2"]
#         mock_file_content = yaml.dump(expected_permissions)
#         def mock_open(*args, **kwargs):
#             class MockFile:
#                 def __enter__(self):
#                     return self
#                 def __exit__(self, *args):
#                     pass
#                 def read(self):
#                     return mock_file_content
#             return MockFile()
#         with unittest.mock.patch('builtins.open', mock_open):
#             result = cloud_reg.get_required_permissions()
#         self.assertEqual(result, expected_permissions)