"""Custom types and type aliases for the validator module.
"""

import re
import enum
from abc import abstractmethod, abstractstaticmethod, ABCMeta
from pathlib import Path
from typing import Dict, Optional, List, Tuple, Any, Union

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

# Type alias for validator module parameters.
ValidatorModuleParams = Dict[str, Any]

# Type alias for manifest data.
Manifest = Dict[str, Any]

# Type alias for report file parameter.
ReportFile = Tuple[Path, Literal["csv", "html", "json", "latex"]]

# Type alias for list of tasks to run.
RunList = Union[Literal["all"], List[str]]


class ValidatorModuleException(Exception):
    """Custom exception type for validator modules.

    Args:
        Exception (Exception): Base exception class.
    """

    pass


class Any:
    """A conditional validator that simulates the behavior of the `OR` operator.
    """

    def __init__(self, content: str, patterns: List[str]) -> None:
        """Constructs the `Any` validator.

        Args:
            content (str): The content to search for patterns in.
            patterns (List[str]): The list of patterns to search for.
        """

        self._content = content
        self._patterns = patterns

    def validate(self) -> Tuple[bool, List[str]]:
        """Validates if any of the specified patterns exist in the specified content.

        Returns:
            Tuple[bool, List[str]]: A tuple whose first value indicates if any of the
                patterns exist in the content, and second value is a list of patterns
                that don't exist in the content.
        """

        not_matching: List[str] = []

        for pattern in self._patterns:
            escaped = re.escape(pattern)
            if not re.search(escaped, self._content):
                not_matching.append(pattern)

        return (len(not_matching) != len(self._patterns), not_matching)


class All:
    """A conditional validator that simulates the behavior of the `AND` operator.
    """

    def __init__(self, content: str, patterns: List[str]) -> None:
        """Constructs the `All` validator.

        Args:
            content (str): The content to search for patterns in.
            patterns (List[str]): The list of patterns to search for.
        """

        self._content = content
        self._patterns = patterns

    def validate(self) -> Tuple[bool, List[str]]:
        """Validates if all of the specified patterns exist in the specified content.

        Returns:
            Tuple[bool, List[str]]: A tuple whose first value indicates if all of the
                patterns exist in the content, and second value is a list of patterns
                that don't exist in the content.
        """

        not_matching: List[str] = []

        for pattern in self._patterns:
            escaped = re.escape(pattern)
            if not re.search(escaped, self._content):
                not_matching.append(pattern)

        return (len(not_matching) == 0, not_matching)


class Status(enum.Enum):
    """Indicates the status of the validation"""

    PASS = "PASS ✅"
    FAIL = "FAIL ❌"

    def __str__(self) -> str:
        """Returns the string representation of the current variant.

        Returns:
            str: String representation of the current variant.
        """

        return self.value

    def __eq__(self, other: object) -> bool:
        """Allows checking the equality operator ('==') for the status object.

        Args:
            other (object): The other object to compare with.

        Returns:
            bool: Whether the other object equals the status value.
        """

        return self.value == other


class Stats:
    """Stats for the validator report.
    """

    def __init__(self, total: int, passed: int, failed: int) -> None:
        """Constructs the stats.

        Args:
            total (int): The total number of tasks run.
            passed (int): The number of tasks that passed.
            failed (int): The number of tasks that failed.
        """

        self.total = total
        self.passed = passed
        self.failed = failed

    def has_failures(self) -> bool:
        """Indicates whether any tasks failed.

        Returns:
            bool: Indicates whether any tasks failed.
        """

        return self.failed > 0


class ValidatorResult:
    """The result of the validation module's execution.
    """

    def __init__(self, status: Status, reason: Optional[str] = None, info: Optional[str] = None) -> None:
        """Constructs a validator result.

        Args:
            status (Status): The status of the validation.
            reason (Optional[str], optional): The reason for the status (if any). Defaults to None.
            info (Optional[str], optional): Any additional info from the validator module (if any).
                Defaults to None.
        """

        self._status = status
        self._reason = reason
        self._info = info

    def is_failure(self) -> bool:
        """Indicates if the current result is a failure.

        Returns:
            bool: Whether the result is a failure
        """

        return self._status == Status.FAIL

    @property
    def status(self):
        return self._status

    @property
    def reason(self):
        return self._reason

    @property
    def info(self):
        return self._info


class ValidatorModule(metaclass=ABCMeta):
    """Interface for a validator module

        Classes should inherit this class and override all the specified
        abstract methods to qualify as a validator.
    """

    @abstractstaticmethod
    def validate_schema(params: ValidatorModuleParams) -> ValidatorModuleParams:
        """Validates whether the parameters supplied to the validator module
            comply with the required schema.


        Returns:
            ValidatorModuleParams: The module's parameters.
        """
        ...

    @abstractmethod
    def run(self) -> ValidatorResult:
        """Runs the validation and returns the result

        Returns:
            ValidatorResult: The result of the validation.
        """
        ...
