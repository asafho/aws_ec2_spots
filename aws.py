import os
import sys
import boto3
import time
import socket
from datetime import datetime, timedelta
import argparse
from dateutil.relativedelta import relativedelta

class AWS(object):
    def __init__(self, env_name='temp', termination_time=''):
        self.env_name = env_name
        self.termination_time = termination_time
        self.aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        self.aws_accountID = "123456789"
        self.subnetID = "sub-12432t"
        self.groupID = "sg-123456"
        self.pem_file = "test_pem_file"
        self.c_time = datetime.now().strftime('%H:%M %d/%m/%Y')
        if not self.aws_access_key or not self.aws_secret_key:
            print ('AWS enviroment variables are not set("AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY")')
            sys.exit(2)

        region_name='us-east-1'
        self.ec2 = boto3.resource('ec2',
                             region_name=region_name,
                             aws_access_key_id=self.aws_access_key,
                             aws_secret_access_key=self.aws_secret_key)

        self.ec2_client = boto3.client('ec2',
                             region_name=region_name,
                             aws_access_key_id=self.aws_access_key,
                             aws_secret_access_key=self.aws_secret_key)


    def compare_times(self, tag_time):
        current_time = time.strptime(self.c_time,'%H:%M %d/%m/%Y')
        tag_time = time.strptime(tag_time,'%H:%M %d/%m/%Y')
        return current_time > tag_time


    def create_ec2(self, type='t2.small', number_devices=0, VolumeSize=10, amiID='ami-test', desc="", instance_type='on-demand'):
        instancesCapacity = int(number_devices)
        if instancesCapacity <= 0:
            return []

        print ('creating ec2 instances: ' + amiID)
        instances_ips = []
        envName = self.env_name + desc
        if instance_type == 'spot':
            try:
                envName = envName +"-spot"
                spot_fleet_request = self.ec2_client.request_spot_fleet(
                SpotFleetRequestConfig={
                    "IamFleetRole": "arn:aws:iam::{0}:role/aws-ec2-spot-fleet-tagging-role".format(self.aws_accountID),
                    'AllocationStrategy': "lowestPrice",
                    'Type': 'maintain',
                    'TargetCapacity': instancesCapacity,
                    'SpotPrice': '0.02',
                    'LaunchSpecifications':[
                        self.get_LaunchSpecifications(imageType='t2.small', VolumeSize=VolumeSize, envName=envName, amiID=amiID),
                        self.get_LaunchSpecifications(imageType='t3.small', VolumeSize=VolumeSize, envName=envName, amiID=amiID),
                        self.get_LaunchSpecifications(imageType='m3.medium', VolumeSize=VolumeSize, envName=envName, amiID=amiID),
                        self.get_LaunchSpecifications(imageType='t3.medium', VolumeSize=VolumeSize, envName=envName, amiID=amiID),
                        self.get_LaunchSpecifications(imageType='t2.medium', VolumeSize=VolumeSize, envName=envName, amiID=amiID)
                    ],
                    'TerminateInstancesWithExpiration': False,
                    'ReplaceUnhealthyInstances': False,
                    'ValidUntil': datetime.utcnow().replace(microsecond=0) + timedelta(hours=2)
                })
                print (spot_fleet_request)
                instances_ips = self.get_instances_from_fleet(spot_fleet_request['SpotFleetRequestId'], instancesCapacity)

            except Exception as e:
                print (e)
        else: #on demand ec2
            try:
                instances = self.ec2.create_instances(
                    BlockDeviceMappings=self.get_BlockDeviceMappings(VolumeSize),
                    TagSpecifications=self.get_TagSpecifications(self.env_name + desc),
                    ImageId=amiID,
                    MinCount=instancesCapacity,
                    MaxCount=instancesCapacity,
                    KeyName=self.pem_file,
                    SubnetId=self.subnetID,
                    InstanceType=type)
            except Exception as e:
                print (e)
            for instance in instances:
                instance.wait_until_running()
                instance.load()
                instances_ips.append(instance.private_ip_address)
                print ('waiting for instances to boot: ' + str(instances))


        print ("waiting to port 22")
        for ip in instances_ips:
            print (ip)
            self.ssh_is_ready(ip)

        return instances_ips

    def ssh_is_ready(ip, ssh_port=22):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        try:
            result = sock.connect_ex((ip, ssh_port))
            retries = 10
            while result != 0 and retries > 0:
                time.sleep(5)
                result = sock.connect_ex((ip, ssh_port))
                retries -= 1
        except:
            print ("can't open port {0}".format(ssh_port))

    def get_instances_from_fleet(self, requestID, capacity):
        print ("creating spots")
        response = None
        attemp = 30
        while attemp > 0 and (response == None or len(response['ActiveInstances']) < capacity):
            response = self.ec2_client.describe_spot_fleet_instances(
                SpotFleetRequestId=requestID
            )
            print ("fetching spots details, current spots capacity: {0}\{1}".format(str(len(response['ActiveInstances'])), capacity))
            time.sleep(20)
            attemp -= 1

        intances_ids=[]
        for spot in response['ActiveInstances']:
            intances_ids.append(spot['InstanceId'])

        intances_ips = []
        try:
            reservervations = self.ec2_client.describe_instances(InstanceIds=intances_ids).get('Reservations',[])
            for index in range(len(reservervations)):
                for intances in reservervations[index]['Instances']:
                    intances_ips.append(intances['PrivateIpAddress'])
        except Exception as e:
            print (e)

        self.ec2_client.cancel_spot_fleet_requests(
            SpotFleetRequestIds=[requestID],
            TerminateInstances=False
        )

        print (intances_ips)
        return intances_ips

    def modify_spot_feet_request(self, requestID, newCapacity):
        print ("editing spot fleet capacity")
        print ("changing request to include {0} instances".formaat(newCapacity))
        try:
            self.ec2_client.modify_spot_fleet_request(
                SpotFleetRequestId=requestID,
                TargetCapacity=newCapacity
            )
        except Exception as e:
            print (e)

    def list_ec2(self):
        try:
            self.instances = self.ec2.instances.filter(Filters=[{'Name': 'instance-state-name','Values': ['running','stopped']}])
        except:
            self.instances = []



    def get_tag_value(self, instance, tag_name):
        if instance.tags:
            for tag in instance.tags:
                if tag_name in tag['Key']:
                    return tag['Value']
        return None


    def get_LaunchSpecifications(self, imageType, VolumeSize, envName, amiID):
        return {
                    'SecurityGroups': [
                        {
                            'GroupId': self.groupID,
                        }
                    ],
                    'BlockDeviceMappings': self.get_BlockDeviceMappings(VolumeSize),
                    'TagSpecifications': self.get_TagSpecifications(envName),
                    'ImageId': amiID,
                    "InstanceType": imageType,
                    'KeyName': self.pem_file,
                    'SubnetId': self.subnetID
                }

    def action_by_name(self, action):
        print (action + "_by_name")
        if not self.env_name:
            return
        print (self.env_name)
        stop_list = []
        for instance in self.instances:
            if self.get_tag_value(instance,'enable_automation_api') == 'true':
                if self.env_name in self.get_tag_value(instance, 'Name'):
                    stop_list.append(instance.id)
        self.execute_api(stop_list, action=action)


    def action_by_timer(self, action):
        print ("stop_by_timer")
        stop_list = []
        for instance in self.instances:
            if self.get_tag_value(instance,'enable_automation_api') == 'true':
                termination_time = self.get_tag_value(instance, 'termination_time')
                if termination_time and self.compare_times(termination_time) == True:
                    stop_list.append(instance.id)
        self.execute_api(stop_list, action=action)

    def execute_api(self, IDs_list=[], action='stop'):
        if IDs_list:
            print (IDs_list)
            print ('devices found: '+str(len(IDs_list)))
            chunkSize = 500
            for i in range(0, len(IDs_list), chunkSize):
                chunk = IDs_list[i:i + chunkSize]
                if action == 'stop':
                    self.ec2.instances.filter(InstanceIds=chunk).stop()
                if action == 'terminate':
                    self.ec2.instances.filter(InstanceIds=chunk).terminate()


    def get_BlockDeviceMappings(self, VolumeSize):
        return [
            {
                'DeviceName': '/dev/sda1',
                'Ebs': {
                    'VolumeSize': VolumeSize,
                    'VolumeType': 'gp2'
                }
            },
        ]

    def get_TagSpecifications(self, envName):
        return [
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': envName
                    },
                    {
                        'Key': 'termination_time',
                        'Value': str(self.termination_time)
                    },
                    {
                        'Key': 'enable_automation_api',
                        'Value': 'true'
                    },
                ]
            },
        ]

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="AWS stop/terminate commands")
    parser.add_argument('--command', dest='cmd',choices=['stop_by_timer','stop_by_name','terminate_by_name','terminate_by_timer'], required=True)
    parser.add_argument('--name', dest='env_name', help='execute by name')
    args = parser.parse_args()
    aws = AWS(env_name=args.env_name)
    aws.list_ec2()

    if args.cmd == 'stop_by_timer':
        aws.action_by_timer('stop')
    elif args.cmd == 'stop_by_name':
        aws.action_by_name('stop')
    elif args.cmd == 'terminate_by_timer':
        aws.action_by_timer('terminate')
    elif args.cmd == 'terminate_by_name':
        aws.action_by_name('terminate')
