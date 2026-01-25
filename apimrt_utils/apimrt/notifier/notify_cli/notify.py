from cliff.command import Command
from apimrt.notifier.utils.teams import TeamsNotifier, PotentialAction, Section


class TeamsNotificationCli(Command):
    """Sends notification to teams channel"""

    def get_parser(self, prog_name):
        parser = super(TeamsNotificationCli, self).get_parser(prog_name)
        parser.add_argument("--weburl", type=str, required=True,
                            help="Provide the teams webhook url")
        parser.add_argument("--title", type=str, required=True,
                            help="Provide the title of the notification")
        parser.add_argument("--summary", type=str, required=True,
                            help="Provide the summary of the notification")
        parser.add_argument("--sectitle", type=str, required=True,
                            help="Provide the section title")
        parser.add_argument("--secsubtitle", type=str, required=False,
                            help="Provide the section subtitle", default="concourse notification")
        parser.add_argument("--concourse_url", type=str, required=False,
                            help="Provide the concourse url of the pipeline will default to normal url",
                            default="https://concourse.cf.eu12.hana.ondemand.com")
        return parser

    def take_action(self, parsed_args):
        weburl = parsed_args.weburl
        title = parsed_args.title
        summary = parsed_args.summary
        sectitle = parsed_args.sectitle
        secsubtitle = parsed_args.secsubtitle
        concourse_url = parsed_args.concourse_url
        teams = TeamsNotifier(
            webhook_url=weburl,
            title=title, summary=summary)
        section_data = Section(sectitle, secsubtitle)
        potential_data = PotentialAction(name="View on concourse", action_type="OpenUri")
        potential_data.add_targets(os="default",
                                   uri=concourse_url)
        teams.add_section(section_data)
        teams.add_potential_action(potential_data)
        resp = teams.send_notification()
        if resp.status_code == 200:
            print("Notification Successfully sent")
        else:
            print("Notification Failed")
