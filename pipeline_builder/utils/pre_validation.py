from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from collections import OrderedDict
from rich import print_json
import os
import yaml

# constants

PRODUCTSFOLDER = 'products'
CONFIGDIRNAME = 'config'
DEPLOYMENTSDIRNAME = 'deployments'


class IacPipelineBuilder:

    def __init__(self):
        self.ls_root = None
        if self.isLandscapeRootFolder(os.path.abspath("./../../../../../..")):
            self.ls_root = os.path.abspath("./../../../../../..")

    def isLandscapeRootFolder(self, path):
        for folder in [PRODUCTSFOLDER, CONFIGDIRNAME, DEPLOYMENTSDIRNAME]:
            if not os.path.exists(os.path.join(path, folder)):
                return False
        return True

    def activated_deployments(self):
        deployment_path = os.path.join(self.ls_root, CONFIGDIRNAME, 'deployments.yml')
        if os.path.exists(deployment_path) is False:
            return []
        with open(deployment_path, 'r') as deployment:
            deployments_dict = yaml.safe_load(deployment)
        return deployments_dict['deployments']

    def dependent_deployment_tree(self):
        deployment_list = self.activated_deployments()
        requires_list = []
        my_data=""
        for dep in deployment_list:
            dep_path = os.path.join(self.ls_root, 'products', dep['product'], 'deployments', dep['instance'],
                                    'deployment.yml')
            comp_path = os.path.join(self.ls_root, 'products', dep['product'], 'components', dep['instance'],
                                    'component.yml')
            with open(dep_path, 'r') as dep_meta:
                dep_meta = yaml.safe_load(dep_meta)
            with open(comp_path, 'r') as comp_meta:
                comp_meta = yaml.safe_load(comp_meta)
            requires_list.append({dep['instance']: {'dep_meta': dep_meta, 'comp_meta': comp_meta}})
        for data in requires_list:
            my_data=f"{my_data}\n{data}"
            print(my_data)
        with open("./config/metadata.json","w") as file:
            file.write(my_data)
        return requires_list

    def not_activated_check(self):
        not_activated = []
        required_deployment = []
        dep_tree = self.dependent_deployment_tree()
        activated_deployments = self.activated_deployments()
        activated_dep_list = [item['instance'] for item in activated_deployments]
        for dep_dict in dep_tree:
            for key, value in dep_dict.items():
                if 'requires' in dep_dict[key]['dep_meta'].keys():
                    for require in dep_dict[key]['dep_meta']['requires']:
                        required_deployment.append(require)
        for dep in required_deployment:
            if dep not in activated_dep_list:
                not_activated.append(dep)

        return not_activated

    def generate_pipeline(self):
        if self.ls_root is None:
            raise Exception("Execute from Landscape root")
        activated_deployments = self.activated_deployments()
        #print_json(data=self.dependent_deployment_tree())
        not_activated = self.not_activated_check()
        if len(not_activated) != 0:
            print("The following required deployments are not activated")
            print(not_activated)

    def display_deployment_flow(self, dep_order_dict):
        console = Console()
        data = []
        for deployment, lifecycles in dep_order_dict.items():
            data.append(Panel.fit('----'.join(lifecycles), title=deployment))

        render_list = []
        for items in enumerate(data):
            if items[0] != 0:
                render_list.append("[bold green][/bold green] :heavy_minus_sign:")
            render_list.append(items[1])

        console.print("\n\nVerify the deployment order\n", justify='left', style='red')
        console.print(Columns(render_list), style="green")

