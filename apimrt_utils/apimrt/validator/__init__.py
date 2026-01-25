"""Manifest-based validation utility and framework for the APIM runtime.
"""

from io import StringIO
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional, List, Callable, Tuple

import yaml
import schema
import jinja2
import tzlocal
from prettytable import PrettyTable, SINGLE_BORDER, ALL

from .consts import __SERVER_GROUPS_SCHEMA__, __TASKS_SCHEMA__
from .modules import remoteshell, localshell, apicall
from .types import ValidatorModuleException, Manifest, ReportFile, RunList
from .types import Stats, Status


class Validator:
    """Validator object that parses the manifest and runs the validations.
    """

    def __init__(
        self,
        manifest: Path,
        extra_vars: Dict[str, Any] = {},
        report_file: Optional[ReportFile] = None,
        run: Optional[RunList] = None,
    ) -> None:
        """Creates a new validator for the specified manifest file.

        Args:
            manifest (Path): Path to the manifest file.
            extra_vars (Optional[Dict[str, Any]], optional): Extra variables for Jinja substitution.
                Defaults to {}.
            report_file (Optional[_ReportFile], optional): A tuple that specifies the path to
                a report file to write the results to, as well as the format of the report.
                Defaults to None.
            run (Optional[_RunList]): List of tasks to run. Defaults to None.
                NOTE: If the manifest file already contains a `run` section, and if this parameter
                is not `None`, then the value of this parameter will override the `run` section in
                the manifest file.
        """

        # We validate the manifest's schema preemptively so that we don't need guard clauses later on,
        # and we can just operate on the manifest data directly.
        self._manifest: Optional[Manifest] = None
        self._schema = schema.Schema({
            "name": str,
            schema.Optional("run", default="all"): schema.Or(
                "all",
                list,
            ),
            schema.Optional("server_groups"): __SERVER_GROUPS_SCHEMA__,
            "tasks": __TASKS_SCHEMA__,
        })
        self._report_file = report_file

        with open(manifest, "r", encoding="utf8") as _f:
            try:
                # Render Jinja2 template using provided extra_variables.
                environment = jinja2.Environment()
                template: jinja2.Template = environment.from_string(
                    _f.read(),
                )
                self._manifest: Optional[Manifest] = self._schema.validate(
                    yaml.safe_load(
                        StringIO(template.render(extra_vars)),
                    ),
                )
            except schema.SchemaError as _e:
                print(f"ERROR: {_e}")
                exit(1)

        # Override manifest's "run" list with the run list specified by the caller.
        if run:
            self._manifest["run"] = run

        timestamp = datetime.now(
            tzlocal.get_localzone(),
        ).strftime("%Y-%m-%d %H:%M:%S %Z")

        self._table = PrettyTable()
        self._table.set_style(SINGLE_BORDER)
        self._table.hrules = ALL
        self._table.vrules = ALL
        self._table.title = "{} [{}]".format(
            self._manifest["name"],
            timestamp,
        )
        self._table.field_names = [
            "NAME",
            "DESCRIPTION",
            "MODULE",
            "SERVER GROUP",
            "HOST",
            "INFO",
            "REASON",
            "STATUS",
        ]

    def validate(self) -> Tuple[Stats, str]:
        """TODO: docstring"""

        total = 0
        passed = 0
        failed = 0

        for task in self._manifest["tasks"]:
            if isinstance(self._manifest["run"], list):
                # Skip the current task if it's not in the "run" list.
                if task["name"] not in self._manifest["run"]:
                    continue

            rows: List[List[str]] = []

            # TODO: Refactor this mess.
            for validation in task["validations"]:
                for (module, params) in validation.items():
                    try:
                        if module == "remoteshell":
                            for group in params["groups"]:
                                try:
                                    for host in self._manifest["server_groups"][group]:
                                        validator = remoteshell.RemoteshellValidator(
                                            host=host["host"],
                                            user=host["user"],
                                            private_key=host["private_key"],
                                            params=params,
                                            port=host["port"],
                                        )
                                        res = validator.run()
                                        rows.append([
                                            task["name"],
                                            task["description"],
                                            module,
                                            group,
                                            host["host"],
                                            res.info,
                                            res.reason,
                                            res.status,
                                        ])
                                        total += 1
                                        if res.status == Status.PASS:
                                            passed += 1
                                        else:
                                            failed += 1
                                except KeyError:
                                    print(f"Invalid server group: `{group}`")
                                    exit(1)

                        if module == "localshell":
                            validator = localshell.LocalshellValidator(params)
                            res = validator.run()
                            rows.append([
                                task["name"],
                                task["description"],
                                module,
                                None,
                                "localhost",
                                res.info,
                                res.reason,
                                res.status,
                            ])
                            total += 1
                            if res.status == Status.PASS:
                                passed += 1
                            else:
                                failed += 1

                        if module == "apicall":
                            validator = apicall.ApicallValidator(params)
                            res = validator.run()
                            rows.append([
                                task["name"],
                                task["description"],
                                module,
                                None,
                                "localhost",
                                res.info,
                                res.reason,
                                res.status,
                            ])
                            total += 1
                            if res.status == Status.PASS:
                                passed += 1
                            else:
                                failed += 1

                    except ValidatorModuleException as _e:
                        print(f"ERROR: {_e}")
                        exit(1)

            self._table.add_rows(rows)

        if self._report_file:
            formatters: Dict[str, Callable] = {
                "csv": self._table.get_csv_string,
                "html": self._table.get_html_string,
                "json": self._table.get_json_string,
                "latex": self._table.get_latex_string,
            }
            html_attrs: Dict[str, Any] = {
                "border": 1,
                "style": "width: 100%; border-width: 1px; border-collapse: collapse;",
            }
            try:
                with open(self._report_file[0], "w") as _f:
                    _f.write(formatters[self._report_file[1]](
                        attributes=html_attrs,
                    ))
            except Exception as _e:
                print(f"ERROR: {_e}")
                exit(1)

        return (Stats(total, passed, failed), self._table.get_string())
