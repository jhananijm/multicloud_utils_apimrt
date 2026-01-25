import sys
import logging
from cliff.app import App
from cliff.commandmanager import CommandManager
import warnings

warnings.filterwarnings(action='ignore')


class ApimrtApp(App):

    def __init__(self):
        super(ApimrtApp, self).__init__(
            description='apimrt utils app',
            version='1.0.0',
            command_manager=CommandManager('apimrt'),
            deferred_help=True,
        )

    def initialize_app(self, argv):
        self.LOG.debug('initialize_app')

    def prepare_to_run_command(self, cmd):
        self.LOG.debug('prepare_to_run_command %s', cmd.__class__.__name__)

    def clean_up(self, cmd, result, err):
        self.LOG.debug('clean_up %s', cmd.__class__.__name__)
        if err:
            self.LOG.debug('got an error: %s', err)

    def configure_logging(self):
        super(ApimrtApp, self).configure_logging()
        if self.options.debug:
            logging.getLogger().setLevel(logging.DEBUG)
        else:
            logging.getLogger().setLevel(logging.ERROR)


def main(argv=sys.argv[1:]):
    myapp = ApimrtApp()
    return myapp.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
