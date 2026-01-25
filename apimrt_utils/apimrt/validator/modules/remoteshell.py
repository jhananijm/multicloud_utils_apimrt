"""Validator module that allows running remote commands and validating their output.
"""

from typing import Optional, Dict, Union, Tuple

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

import schema
import paramiko

from ..types import Any, All
from ..types import ValidatorModule, ValidatorModuleException, ValidatorResult
from ..types import Status, ValidatorModuleParams

__STREAMS__: Tuple[Literal["stdout"], Literal["stderr"]] = ("stdout", "stderr")
__STREAM_ERROR__: str = "'stream' must be one of 'stdout' or 'stderr'"
__CONDITIONS__: Tuple[Literal["any"], Literal["all"]] = ("any", "all")
__CONDITION_ERROR__: str = "'condition' must be one of 'any' or 'all'"
__SCHEMA__ = schema.Schema({
    "command": str,
    schema.Optional("stream", default="stdout"): schema.And(
        str,
        schema.Use(str.lower),
        lambda s: s in __STREAMS__,
        error=__STREAM_ERROR__,
    ),
    schema.Optional("contains", default=None): {
        "strings": list,
        schema.Optional("condition", default="all"): schema.And(
            str,
            schema.Use(str.lower),
            lambda s: s in __CONDITIONS__,
            error=__CONDITION_ERROR__,
        ),
    },
    schema.Optional("not_contains", default=None): {
        "strings": list,
        schema.Optional("condition", default="all"): schema.And(
            str,
            schema.Use(str.lower),
            lambda s: s in __CONDITIONS__,
            error=__CONDITION_ERROR__,
        ),
    },
    "groups": list,
})


class RemoteshellValidator(ValidatorModule):
    """The remote shell validator module.

    Args:
        ValidatorModule (ValidatorModule): The base validator module interface.
    """

    def __init__(
        self,
        host: str,
        user: str,
        private_key: str,
        params: ValidatorModuleParams,
        port: int = 22,
        timeout: int = 10,
    ) -> None:
        """Constructs the remote shell validator.

        Args:
            host (str): The host name/address.
            user (str): The SSH user name.
            private_key (str): The path to the SSH private key.
            params (ValidatorModuleParams): The parameters for the module.
            port (int, optional): The SSH port. Defaults to 22.
            timeout (int, optional): The connection timeout in seconds. Defaults to 10.

        Raises:
            ValidatorModuleException: When the parameters' schema is invalid.
            ValidatorModuleException: When the private key file is not found.
        """

        try:
            self._params = self.validate_schema(params)
        except schema.SchemaError as _e:
            raise ValidatorModuleException(_e)

        self._host = host
        self._user = user

        try:
            self._private_key = paramiko.RSAKey.from_private_key_file(
                private_key,
            )
        except FileNotFoundError:
            raise ValidatorModuleException(
                f"Private key `{private_key}` not found.",
            )

        self._port = port

        # Connect to remote host.
        self._ssh = paramiko.SSHClient()
        self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._ssh.connect(
            self._host,
            self._port,
            self._user,
            pkey=self._private_key,
            timeout=timeout,
        )

    def __del__(self):
        """Cleans up the module by closing the SSH connection (if established).
        """

        try:
            self._ssh.close()
        except AttributeError:
            pass

    @staticmethod
    def validate_schema(params: ValidatorModuleParams) -> ValidatorModuleParams:
        """Validates the schema of the parameters.

        Args:
            params (ValidatorModuleParams): The module's parameters.

        Returns:
            ValidatorModuleParams: The module's parameters (with filled in defaults).
        """

        return __SCHEMA__.validate(params)

    def run(self) -> ValidatorResult:
        """Runs the validator module.

        Returns:
            ValidatorResult: The result of the validation task.
        """

        # By default, we assume the validation has passed.
        status: Status = Status.PASS
        output: Optional[str] = None
        reason: Optional[str] = None

        # Conditional validators.
        conditions: Dict[str, Union[Any, All]] = {
            "any": Any,
            "all": All,
        }

        # Execute the command and retrieve its stdout, stderr and exit status.
        _, stdout, stderr = self._ssh.exec_command(self._params["command"])
        exit_status = stdout.channel.recv_exit_status()

        # If the exit status is non-zero, it indicates a failure in executing the command.
        # In that case, the validation has failed. We retrieve the failure reason from stderr.
        if exit_status != 0:
            status = Status.FAIL
            reason = stderr.read().decode("utf-8")

        # We retrieve now the content from the required stream.
        if self._params["stream"] == "stderr":
            output = stderr.read().decode("utf-8") or ""
        else:
            output = stdout.read().decode("utf-8") or ""

        # If the user has specified a "contains" constraint, we validate it.
        if self._params["contains"]:
            (res, not_matching) = conditions[self._params["contains"]["condition"]](
                output, self._params["contains"]["strings"],
            ).validate()
            if not res:
                status = Status.FAIL
                reason = f"The following patterns were not found in the command output: {not_matching}"

        # If the user has specified a "not_contains" constraint, we validate it.
        if self._params["not_contains"]:
            (res, matches) = conditions[self._params["not_contains"]["condition"]](
                output, self._params["not_contains"]["strings"],
            ).validate()
            if res:
                status = Status.FAIL
                # XOR to get the list of strings that were contained in the output.
                matches = set(matches) ^ set(
                    self._params["not_contains"]["strings"],
                )
                reason = f"The following patterns were found in the command output: {matches}"

        return ValidatorResult(status, reason=reason, info=output)
