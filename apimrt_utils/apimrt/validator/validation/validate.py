from apimrt.validator import Validator
from apimrt.validator.validation.extra import inv_to_dict, print_color, COMPONENT_LIST, COMPONENT_TASKS, \
    DEFAULT_INVENTORY_PATH, DEFAULT_VALIDATIONS_FOLDER, APIMRT_MODULES


class ValidationClass:
    def __init__(self, component_list=COMPONENT_LIST, component_tasks=COMPONENT_TASKS):
        self.component_list = component_list
        self.component_tasks = component_tasks
        self.validation_failure = False

    def validator(self, inv, ev, folder_path, optional_components=None):
        component_list = list(inv.keys())
        component_list.append("localhost")
        if optional_components:
            component_list = []
            for opt_comp in optional_components:
                if opt_comp in inv.keys() or opt_comp == "localhost":
                    component_list.append(opt_comp)
                else:
                    print(f"Component {opt_comp} not present in inventory")

        for component in component_list:
            if component == "localhost":
                print(f"Validating {component}")
                ev['tasks'] = self.component_tasks[f"localhost_{ev['landscape_type']}"]
                ev['apimrt_modules'] = APIMRT_MODULES
                val = Validator(
                    manifest=f"{folder_path}/{component}.yml.j2", extra_vars=ev)
                (stats, report) = val.validate()
                print(report)
                if stats.has_failures():
                    print_color(
                        f"==> Error: {component} Validation failed", "\033[91m")
                    self.validation_failure = True
                break

            for ip in inv[component]:
                print(f"Validating IP {ip} of component {component}")
                ev['component_type'] = component
                ev[f'{component}_ip'] = ip
                ev['tasks'] = self.component_tasks[f"common_{ev['landscape_type']}"]
                val = Validator(
                    manifest=f"{folder_path}/common.yml.j2", extra_vars=ev)
                (stats, report) = val.validate()
                print(report)
                if stats.has_failures():
                    print_color(
                        "==> Error: Common Validation failed", "\033[91m")
                    self.validation_failure = True
                if f"{component}_{ev['landscape_type']}" not in self.component_tasks:
                    continue
                ev['tasks'] = self.component_tasks[f"{component}_{ev['landscape_type']}"]
                val = Validator(
                    manifest=f"{folder_path}/{component}.yml.j2", extra_vars=ev)
                (stats, report) = val.validate()
                print(report)
                if stats.has_failures():
                    print_color(
                        f"==> Error: {component} Validation failed", "\033[91m")
                    self.validation_failure = True

    def validate(self, extra_var, validations_folder=DEFAULT_VALIDATIONS_FOLDER, inv_path=DEFAULT_INVENTORY_PATH,
                 optional_components=None):
        inventory = inv_to_dict(inv_path)
        ev = extra_var
        self.validator(inv=inventory, ev=ev, folder_path=validations_folder,
                       optional_components=optional_components)
        if self.validation_failure:
            print_color(
                "!!!!!  ERROR found in Validation. Please refer to the report and make necessary changes  !!!!!",
                "\033[91m")
            exit(1)
