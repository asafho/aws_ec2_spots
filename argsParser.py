from argparse import (ArgumentParser,
                      RawTextHelpFormatter)

__author__ = 'asafh'


class ArgParser(ArgumentParser):
    def __init__(self):
        description = 'New build parameters.'
        super(ArgParser, self).__init__(description=description,
                                        formatter_class=RawTextHelpFormatter)

    def parse_args(self):

        self.add_argument('--server',
                          action='store',
                          type=str,
                          dest='server',
                          default='m4.large',
                          help='aws server type(ip or valid ec2 type)')
        self.add_argument('--ec2_ami',
                          action='store',
                          type=str,
                          dest='ami',
                          default='ami-dgsfdggfaa',
                          help='aws server ami')

        self.add_argument('--env-name',
                          action='store',
                          type=str,
                          dest='env_name',
                          default='temp_env',
                          help='enviroment name')

        self.add_argument('--timer',
                          action='store',
                          dest='timer',
                          default=5,
                          type=int,
                          help='timer for enviroment termination (hours)')

        return super(ArgParser, self).parse_args()
