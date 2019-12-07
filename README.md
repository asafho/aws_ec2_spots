# aws_ec2_spots
script to create/stop/terminate AWS ec2/spots

### prerequisites
install requirements.txt file
set environment variables with your AWS keys
 - AWS_ACCESS_KEY_ID
 - AWS_SECRET_ACCESS_KEY
 
 
setup your account details in aws.py
 - self.aws_accountID = "123456789"
 - self.subnetID = "sub-12432t"
 - self.groupID = "sg-123456"
 - self.pem_file = "test_pem_file"
 
 
#### create ec2/spot
python main.py 

#### terminate aws server by timer
python aws.py --command terminate_by_timer <br />
this will terminate all lives servers that passed the timer on boot 

#### stop aws server by timer
python aws.py --command stop_by_timer <br />
this will stop all lives servers that passed the timer on boot 


#### terminate aws server by name
python aws.py --command terminate_by_name --name testname <br />
this will terminate all lives servers that contains the given name

#### stop aws server by name
python aws.py --command stop_by_name --name testname <br />
this will stop all lives servers that contains the given name 
