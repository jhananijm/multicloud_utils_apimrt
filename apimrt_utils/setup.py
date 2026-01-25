from setuptools import find_packages, find_namespace_packages
from setuptools import setup

PROJECT = 'apimrt'


def get_version():
    with open('version.txt') as ver_file:
        version_str = ver_file.readline().rstrip()
    return version_str


def get_install_requires(key):
    reqs = []
    with open(f'{key}requirements.txt') as reqs_file:
        for line in iter(lambda: reqs_file.readline().rstrip(), ''):
            reqs.append(line)
    return reqs


extras_require = {
    'apim-aws': get_install_requires('aws-'),
    'apim-azure': get_install_requires('azure-'),
    'apim-gcp': get_install_requires('gcp-'),
    'apim-alibaba': get_install_requires('alibaba-'),
    'apim-cc3': get_install_requires('cc3-')
}

# List the packages to exclude based on the type passed as an extras requirement
EXCLUDE_PACKAGES = {
    'apim-aws': ['apimrt.clouds.alibaba', 'apimrt.clouds.azure', 'apimrt.clouds.gcp', 'apimrt.clouds.cc3'],
    'apim-azure': ['apimrt.clouds.alibaba', 'apimrt.clouds.aws', 'apimrt.clouds.gcp', 'apimrt.clouds.cc3'],
    'apim-alibaba': ['apimrt.clouds.azure', 'apimrt.clouds.aws', 'apimrt.clouds.gcp', 'apimrt.clouds.cc3'],
    'apim-cc3': ['apimrt.clouds.azure', 'apimrt.clouds.aws', 'apimrt.clouds.gcp', 'apimrt.clouds.alibaba'],
    'apim-gcp': ['apimrt.clouds.azure', 'apimrt.clouds.aws', 'apimrt.clouds.cc3', 'apimrt.clouds.alibaba']
}

exclude_packages = []

for req in extras_require.get('type', []):
    exclude_packages.extend(EXCLUDE_PACKAGES.get(req, []))
try:
    long_description = open('README.rst', 'rt').read()
except IOError:
    long_description = ''

setup(
    name=PROJECT,
    version=get_version(),

    description='utils for apigee',
    long_description=long_description,

    author='apimrt',
    author_email='DL_606EA768654D33027ECC2B0B@global.corp.sap',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Intended Audience :: Developers',
        'Environment :: Console',
    ],

    platforms=['Any'],

    scripts=[],

    provides=[],
    install_requires=get_install_requires(''),
    package_data={'apimrt': ['apigee/cassandra/config/*.yml', 'clouds/aws/data/*.yml', 'clouds/azure/data/*.yml',
                             'clouds/alibaba/data/*.yml', 'clouds/gcp/data/*.yml', 'clouds/cc3/data/*.yml',
                             'validator/validations/*', 'custom_props/config/*.yml',
                             ]},
    namespace_packages=[],
    packages=find_namespace_packages(),
    include_package_data=True,
    zip_safe=False,
    extras_require=extras_require,
    entry_points={
        'console_scripts': [
            'apimrt = apimrt.main:main'
        ],
        'apimrt': [
            'casstools_compact_validate = apimrt.apigee.cassandra.cass_cli:CompactionValidation',
            'casstools_gen_alter = apimrt.apigee.cassandra.cass_cli:AlterCmdGenerator',
            'casstools_gen_rebuild = apimrt.apigee.cassandra.cass_cli:RebuildCmdGenerator',
            'cloud_type = apimrt.common_cloud.common_cloud_cli:GetCloudType',
            'cloud_project = apimrt.common_cloud.common_cloud_cli:GetProjectName',
            'cloud_instance_name_get = apimrt.common_cloud.common_cloud_cli:GetInstanceNameFromIPAndProjectName',
            'cloud_project_instance_name_get = apimrt.common_cloud.common_cloud_cli:GetInstanceNameFromIP',
            'cloud_instance_tags_get = apimrt.common_cloud.common_cloud_cli:GetInstanceTags',
            'cloud_secrets_get = apimrt.common_cloud.common_cloud_cli:GetSecret',
            'cloud_secrets_update = apimrt.common_cloud.common_cloud_cli:UpdateSecrets',
            'cloud_project_secret = apimrt.common_cloud.common_cloud_cli:GetProjectSecretName',
            'cloud_scalinggroups_get = apimrt.common_cloud.common_cloud_cli:GetScalingGroups',
            'cloud_permission_available_get = apimrt.common_cloud.common_cloud_cli:GetAvailablePermissions',
            'cloud_permission_required_get = apimrt.common_cloud.common_cloud_cli:GetRequiredPermissions',
            'cloud_permission_missing_get  = apimrt.common_cloud.common_cloud_cli:PerformPermissionCheck',
            'cloud_volume_snapshot = apimrt.common_cloud.common_cloud_cli:TakeVolumeSnapshot',
            'cloud_image_update = apimrt.common_cloud.common_cloud_cli:UpdateImage',
            'validate = apimrt.validator.cli:ValidatorCLI',
            'validation_list = apimrt.validator.cli:ValidationListerCLI',
            'validation = apimrt.validator.cli:ValidationCLI',
            'silentconfig_generate = apimrt.silent_config.cli:SilentConfigCLI',
            'notify_teams = apimrt.notifier.notify_cli.notify:TeamsNotificationCli',
            'custom_props_modify = apimrt.custom_props.cli:CustomPropsCLI'
        ],
    },
)
