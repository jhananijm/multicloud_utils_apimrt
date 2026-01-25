"""Validator module that allows running local commands and validating their output.
"""

import shlex
import subprocess
from subprocess import CompletedProcess
from typing import Tuple, Optional, Dict, Union

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

import schema

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
})


class LocalshellValidator(ValidatorModule):
    """TODO: docstring"""

    def __init__(self, params: ValidatorModuleParams) -> None:
        """TODO: docstring"""

        try:
            self._params = self.validate_schema(params)
        except schema.SchemaError as _e:
            raise ValidatorModuleException(_e)

    @staticmethod
    def validate_schema(params: ValidatorModuleParams) -> ValidatorModuleParams:
        """TODO: docstring"""

        return __SCHEMA__.validate(params)

    def run(self) -> ValidatorResult:
        """TODO: docstring"""

        # By default, we assume the validation has passed.
        status: Status = Status.PASS
        output: Optional[str] = None
        reason: Optional[str] = None

        # Conditional validators.
        conditions: Dict[str, Union[Any, All]] = {
            "any": Any,
            "all": All,
        }

        # Execute command and retrieve its stdout, stderr and exit status.
        out: CompletedProcess[str] = subprocess.run(
            shlex.split(self._params["command"]),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if out.returncode != 0:
            status = Status.FAIL
            reason = out.stderr

        # We now retrieve the content from the required stream.
        if self._params["stream"] == "stderr":
            output = out.stderr
        else:
            output = out.stdout

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
