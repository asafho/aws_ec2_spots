import os
import argsParser
from datetime import datetime
from dateutil.relativedelta import relativedelta
import socket
import time
from aws import AWS

__author__ = 'asafh'


class Env(object):
    def __init__(self):

        args = argsParser.ArgParser().parse_args()
        self.env_name = args.env_name
        self.timer = args.timer
        self.server_type = args.server
        self.ami = args.ami
        self.termination_time = self.set_timer()
        self.aws = AWS(env_name=self.env_name, termination_time=self.termination_time)

    def set_timer(self):
        print ('========================================================')
        c_time = datetime.now().strftime('%H:%M %d/%m/%Y')
        termination_time = (datetime.now() + relativedelta(hours=self.timer)).strftime('%H:%M %d/%m/%Y')
        print ('current time: ' + c_time)
        print ("enviroment will terminate at: " + termination_time)
        print ('========================================================')
        return termination_time

def create_ec2(env):
    print ("creating ec2 machine as server")
    env.server_ip = env.env.aws.create_ec2(type=type,
                                                 number_devices=1,
                                                 VolumeSize=10,
                                                 amiID=env.ami,
                                                 desc="_server")[0]
    time.sleep(20)
    print ("=========================================================")
    print ("             ec2 server ip: " + env.server_ip)
    print ("=========================================================")

def create_spots(env):
    print ("creating spots machine as server")
    env.servers_ip = env.env.aws.create_ec2(type=type,
                                                 number_devices=2,
                                                 VolumeSize=10,
                                                 amiID=env.ami,
                                                 desc="_spot",
                                                 instance_type='spot')

    print ("=========================================================")
    print ("             spots servers ip: " + env.servers_ip)
    print ("=========================================================")

if __name__ == '__main__':
    env = Env()
    create_ec2(env)
    create_spots(env)