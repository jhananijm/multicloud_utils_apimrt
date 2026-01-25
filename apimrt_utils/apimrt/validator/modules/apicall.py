"""Validator module that allows making API calls and validating the response.
"""

import json
from typing import Optional, Dict, Union, Tuple

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

import schema
import urllib3

from ..types import Any, All
from ..types import ValidatorModule, ValidatorModuleException, ValidatorResult
from ..types import Status, ValidatorModuleParams

__PROTOCOLS__: Tuple[Literal["http"], Literal["https"]] = ("http", "https")
__PROTOCOL_ERROR__: str = "'protocol' must be one of 'http' or 'https'"
__CONDITIONS__: Tuple[Literal["any"], Literal["all"]] = ("any", "all")
__CONDITION_ERROR__: str = "'condition' must be one of 'any' or 'all'"
__SCHEMA__ = schema.Schema({
    schema.Optional("protocol", default="http"): schema.And(
        str,
        schema.Use(str.lower),
        lambda s: s in __PROTOCOLS__,
        error=__PROTOCOL_ERROR__,
    ),
    "host": str,
    schema.Optional("port", default=80): int,
    schema.Optional("path", default="/"): str,
    schema.Optional("method", default="GET"): str,
    schema.Optional("response", default=200): int,
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
    schema.Optional("headers", default=None): {
        str: str,
    },
    schema.Optional("auth", default=None): {
        "user": str,
        "password": str,
    },
    schema.Optional("timeout", default=10): int,
    schema.Optional("poll", default=None): {
        schema.Optional("counts", default={"total": 10}): {
            schema.Optional("total", default=10): int,
            schema.Optional("connect", default=None): int,
            schema.Optional("read", default=None): int,
            schema.Optional("redirect", default=None): int,
            schema.Optional("status", default=None): int,
            schema.Optional("other", default=None): int,
        },
        schema.Optional(
            "allowed_methods",
            default=urllib3.Retry.DEFAULT_ALLOWED_METHODS,
        ): list,
        schema.Optional("status_forcelist", default=None): list,
        schema.Optional("backoff_factor", default=0.0): float,
        schema.Optional("raise_on_redirect", default=True): bool,
        schema.Optional("raise_on_status", default=True): bool,
        schema.Optional("history", default=None): tuple,
        schema.Optional("respect_retry_after_header", default=True): bool,
        schema.Optional(
            "remove_headers_on_redirect",
            default=urllib3.Retry.DEFAULT_REMOVE_HEADERS_ON_REDIRECT,
        ): list,
    },
})


class ApicallValidator(ValidatorModule):
    """The api call validator module.

    Args:
        ValidatorModule (ValidatorModule): The base validator module interface.
    """

    def __init__(self, params: ValidatorModuleParams) -> None:
        """Constructs the api call validator.

        Args:
            params (ValidatorModuleParams): The parameters for the module.

        Raises:
            ValidatorModuleException: When the parameters' schema is invalid.
        """

        try:
            self._params = self.validate_schema(params)
        except schema.SchemaError as _e:
            raise ValidatorModuleException(_e)

        # Create new connection pool and configure it.
        headers: Dict[str, str] = {}
        # Add headers if specified.
        if self._params["headers"]:
            headers.update(self._params["headers"])
        # Add auth headers if specified.
        if self._params["auth"]:
            headers.update(urllib3.make_headers(basic_auth="{}:{}".format(
                self._params["auth"]["user"],
                self._params["auth"]["password"],
            )))
        # Configure retries if polling is specified.
        retries = False
        if self._params["poll"]:
            retries = urllib3.util.Retry(
                total=self._params["poll"]["counts"]["total"],
                connect=self._params["poll"]["counts"]["connect"],
                read=self._params["poll"]["counts"]["read"],
                redirect=self._params["poll"]["counts"]["redirect"],
                status=self._params["poll"]["counts"]["status"],
                other=self._params["poll"]["counts"]["other"],
                allowed_methods=self._params["poll"]["allowed_methods"],
                status_forcelist=self._params["poll"]["status_forcelist"],
                backoff_factor=self._params["poll"]["backoff_factor"],
                raise_on_redirect=self._params["poll"]["raise_on_redirect"],
                raise_on_status=self._params["poll"]["raise_on_status"],
                history=self._params["poll"]["history"],
                respect_retry_after_header=self._params["poll"]["respect_retry_after_header"],
                remove_headers_on_redirect=self._params["poll"]["remove_headers_on_redirect"],
            )
        self._pool = urllib3.PoolManager(
            timeout=urllib3.Timeout(
                total=self._params["timeout"],
            ),
            retries=retries,
            headers=headers,
        )

    def __del__(self):
        """Cleans up the module by closing the request session (if established).
        """

        try:
            self._pool.clear()
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
        reason: Optional[str] = None
        info: Optional[str] = None
        body: str = ""

        # Conditional validators.
        conditions: Dict[str, Union[Any, All]] = {
            "any": Any,
            "all": All,
        }

        # Form the URL from the provided params.
        url = "{}://{}:{}/{}".format(
            self._params["protocol"],
            self._params["host"],
            self._params["port"],
            self._params["path"],
        )

        # Make request and parse output.
        resp: urllib3.response.HTTPResponse = self._pool.request(
            method=self._params["method"],
            url=url,
        )
        body = resp.data.decode("utf-8")
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            pass

        # If the response status code does not match what the user has specified,
        # the validation has failed.
        if resp.status != self._params["response"]:
            status = Status.FAIL
            reason = body

        # If the user has specified a "contains" constraint, we validate it.
        if self._params["contains"]:
            (res, matches) = conditions[self._params["contains"]["condition"]](
                body, self._params["contains"]["strings"],
            ).validate()
            if not res:
                status = Status.FAIL
                reason = f"The following patterns were not found in the response body: {matches}"

        # If the user has specified a "not_contains" constraint, we validate it.
        if self._params["not_contains"]:
            (res, matches) = conditions[self._params["not_contains"]["condition"]](
                body, self._params["not_contains"]["strings"],
            ).validate()
            if res:
                status = Status.FAIL
                # XOR to get the list of strings that were contained in the response body.
                matches = set(matches) ^ set(
                    self._params["not_contains"]["strings"],
                )
                reason = f"The following patterns were found in the response body: {matches}"

        info = resp.status
        resp.close()

        return ValidatorResult(status, reason=reason, info=info)
