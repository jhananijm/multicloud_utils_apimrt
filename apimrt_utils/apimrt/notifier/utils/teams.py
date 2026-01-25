import requests


class Section:
    def __init__(self, activity_title, activity_subtitle):
        self.activity_title = activity_title
        self.activity_subtitle = activity_subtitle
        self.facts = []

    def add_fact(self, name, value):
        self.facts.append({"name": name, "value": value})


class PotentialAction:
    def __init__(self, name, action_type):
        self.name = name
        self.action_type = action_type
        self.targets = []

    def add_targets(self, **kwargs):
        self.targets.append(kwargs)


class TeamsNotifier:
    def __init__(self, webhook_url, title, summary, color="0072C6"):
        self.webhook_url = webhook_url
        self.title = title
        self.summary = summary
        self.color = color
        self.sections = []
        self.facts = []
        self.potential_actions = []

    def add_section(self, section):
        section_dict = {
            "activityTitle": section.activity_title,
            "activitySubtitle": section.activity_subtitle,
            "facts": section.facts
        }
        self.sections.append(section_dict)

    def add_potential_action(self, potential_action):
        potential_action_dict = {
            "name": potential_action.name,
            "@type": potential_action.action_type,
            "targets": potential_action.targets

        }
        self.potential_actions.append(potential_action_dict)

    def send_notification(self, notifier_type="MessageCard", context="https://schema.org/extensions"):
        payload_dict = {
            "@type": notifier_type,
            "@context": context,
            "themeColor": self.color,
            "summary": self.summary,
            "title": self.title,
            "sections": self.sections,
            "potentialAction": self.potential_actions,
        }
        resp = requests.post(self.webhook_url, json=payload_dict, verify=False)
        return resp


