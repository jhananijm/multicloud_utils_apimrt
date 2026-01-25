"""Constant values for the validator module.
"""

import schema

# The schema of the host definition.
#
# Example:
#
# host: 192.168.0.1
# user: concourseci
# private_key: /etc/ansible/priv
# port: 2222 (optional field, defaults to 22)
__HOST_SCHEMA__ = {
    "host": str,
    "user": str,
    "private_key": str,
    schema.Optional("port", default=22): int,
}

# The schema of the "server_groups" section of the manifest.
#
# This section must be a dictionary whose keys are the names of the server groups, and the values
# can either be a list of host detail dictionaries, or a dictionary of dictionaries. In the case
# where the value is a dictionary of dictionaries, the keys of this dictionary must be the name of
# the host, and the values should be the host detail dictionaries.
#
# Examples:
#
# msui:
#   - host: 192.168.0.1
#     user: concourseci
#     private_key: /etc/ansible/priv
#     port: 2222
#   - host: 192.168.0.2
#     user: concourseci
#     private_key: /etc/ansible/priv
#
#  OR
#
# msui:
#   msui_1:
#     host: 192.168.0.1
#     user: concourseci
#     private_key: /etc/ansible/priv
#     port: 2222
#   msui_2:
#     host: 192.168.0.1
#     user: concourseci
#     private_key: /etc/ansible/priv
#
# NOTE: It is possible to use a mixture of these formats.
# i.e. One server group can use the list of dictionaries format, and the other group(s) can use the
# dictionary of dictionaries format.
__SERVER_GROUPS_SCHEMA__ = {
    str: schema.Or(
        [__HOST_SCHEMA__],
        {str: __HOST_SCHEMA__},
    ),
}

# The schema of the list of tasks.
#
# Example:
#
# - name: validate_echo
#   description: Validates if the echo command works
#   validations:
#     validation_module:
#       validation_module_params...
#  - name: validate_response
#    description: Validates if a request succeeds
#    validations:
#      validation_module:
#        validation_module_params...
__TASKS_SCHEMA__ = schema.Schema(
    [{
        "name": schema.And(
            str,
            schema.And(
                lambda s: ' ' not in s,
                error="'name' must not contain any spaces (use _ instead)",
            ),
            error="'name' field is missing/contains invalid value",
        ),
        "description": schema.And(str, error="'description' field is mandatory"),
        "validations": [{
            str: any,
        }],
    }])
