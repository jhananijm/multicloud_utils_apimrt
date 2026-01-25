from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns

class Display:
    def __init__(self):
        pass

    def print_table(self, column_name, data):
        console = Console()
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column(column_name, style="cyan", width=20)
        for i in data:
            table.add_row(i, style="bold")
        console.print(table)

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