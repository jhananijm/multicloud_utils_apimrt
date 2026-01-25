import copy

COMPONENT_LIST = ['ms', 'pg', 'qpid', 'ldap', 'zkcs', 'localhost']

COMPONENT_TASKS = {
    'ms_prod': ['validate_apigee_all_status_for_ms', 'validate_custom_property_files', 'validate_password'],
    'pg_prod': ['validate_apigee_all_status_for_pg', 'validate_custom_property_files', 'validate_password','check_max_lock_per_transaction','check_max_connections'],
    'qpid_prod': ['validate_apigee_all_status_for_qpid', 'validate_if_queue_is_present', 'validate_max_queue_size',
                  'validate_custom_property_files'],
    'common_prod': ['validate_dynatrace', 'validate_trendmicro', 'validate_audit_logging',
                    'os_version_check', 'apigee_version_check', 'cpu_check', 'mem_check', 'disk_check', 'cpu_load', 'disk_check_apigee','apigee_service_check'],
    'ldap_prod': ['validate_password'],
    'zkcs_prod': ['heap_mem_check', 'cassandra_ring_check', 'cassandra_status_check','nodetool_patching_status'],
    'localhost_prod': ['ansible_version', 'check_apimrt_modules'],

    'ms_dev': ['validate_apigee_all_status_for_ms', 'validate_custom_property_files', 'validate_password'],
    'pg_dev': ['validate_apigee_all_status_for_pg', 'validate_custom_property_files', 'validate_password','check_max_lock_per_transaction','check_max_connections'],
    'qpid_dev': ['validate_apigee_all_status_for_qpid', 'validate_if_queue_is_present', 'validate_max_queue_size',
                 'validate_custom_property_files'],
    'common_dev': ['validate_dynatrace',
                   'os_version_check', 'apigee_version_check', 'cpu_check', 'mem_check', 'disk_check', 'cpu_load', 'disk_check_apigee','apigee_service_check'],
    'ldap_dev': ['validate_password'],
    'zkcs_dev': ['heap_mem_check', 'cassandra_ring_check', 'cassandra_status_check','nodetool_patching_status'],
    'localhost_dev': ['ansible_version', 'check_apimrt_modules'],
}

DEFAULT_INVENTORY_PATH = "./inputs/inventory"

DEFAULT_VALIDATIONS_FOLDER = "../validations"

APIMRT_MODULES = [
    "casstools compact validate",
    "casstools gen alter",
    "casstools gen rebuild",
    "cloud image update",
    "cloud instance name get",
    "cloud instance tags get",
    "cloud permission available get",
    "cloud permission missing get",
    "cloud permission required get",
    "cloud project",
    "cloud project instance name get",
    "cloud project secret",
    "cloud scalinggroups get",
    "cloud secrets get",
    "cloud secrets update",
    "cloud type",
    "cloud volume snapshot",
    "notify teams",
    "silentconfig generate",
    "validate",
    "validation",
    "validation list",
]


def inv_to_dict(inv_path):
    # inv to dict code block
    value = []
    flag = 0
    inv = {}

    with open(inv_path, 'r') as file:
        data = file.read()

    for d in data.split("\n"):
        if "[" in d:
            if flag != 0:
                inv[key] = copy.deepcopy(value)
                value.clear()
            key = d.replace("[", "").replace("]", "")
            flag = 1
        else:
            if d is not '':
                value.append(d)
    inv[key] = value
    return inv


def print_color(text, color_code):
    print(f"{color_code}{text}\033[0m")
