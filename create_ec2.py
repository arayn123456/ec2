#!/usr/bin/env python3
"""Create an EC2 instance using configuration from a .env file."""

import os
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv


def load_config() -> dict:
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print(f"Error: .env file not found at {env_path}")
        print("Copy .env.example to .env and fill in your values.")
        sys.exit(1)

    load_dotenv(env_path)

    required = [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_REGION",
        "AMI_ID",
        "INSTANCE_TYPE",
        "KEY_NAME",
        "SUBNET_ID",
        "IAM_INSTANCE_PROFILE",
    ]

    missing = [key for key in required if not os.getenv(key)]
    if missing:
        print(f"Error: missing required .env variables: {', '.join(missing)}")
        sys.exit(1)

    sg_ids = os.getenv("SECURITY_GROUP_IDS", "").strip()
    security_group_ids = [sg.strip() for sg in sg_ids.split(",") if sg.strip()]

    associate_public_ip = os.getenv("ASSOCIATE_PUBLIC_IP", "true").lower() in ("true", "1", "yes")

    return {
        "region": os.getenv("AWS_REGION"),
        "ami_id": os.getenv("AMI_ID"),
        "instance_type": os.getenv("INSTANCE_TYPE"),
        "key_name": os.getenv("KEY_NAME"),
        "subnet_id": os.getenv("SUBNET_ID"),
        "vpc_id": os.getenv("VPC_ID"),
        "security_group_ids": security_group_ids or None,
        "iam_instance_profile": os.getenv("IAM_INSTANCE_PROFILE"),
        "associate_public_ip": associate_public_ip,
        "instance_name": os.getenv("INSTANCE_NAME", "ec2-instance"),
        "volume_size_gb": int(os.getenv("VOLUME_SIZE_GB", "8")),
    }


def create_ec2_instance(config: dict) -> dict:
    session = boto3.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=config["region"],
    )
    ec2 = session.client("ec2")

    network_interface = {
        "DeviceIndex": 0,
        "SubnetId": config["subnet_id"],
        "AssociatePublicIpAddress": config["associate_public_ip"],
    }
    if config["security_group_ids"]:
        network_interface["Groups"] = config["security_group_ids"]

    run_params = {
        "ImageId": config["ami_id"],
        "InstanceType": config["instance_type"],
        "KeyName": config["key_name"],
        "MinCount": 1,
        "MaxCount": 1,
        "NetworkInterfaces": [network_interface],
        "IamInstanceProfile": {"Name": config["iam_instance_profile"]},
        "BlockDeviceMappings": [
            {
                "DeviceName": "/dev/xvda",
                "Ebs": {
                    "VolumeSize": config["volume_size_gb"],
                    "VolumeType": "gp3",
                    "DeleteOnTermination": True,
                },
            }
        ],
        "TagSpecifications": [
            {
                "ResourceType": "instance",
                "Tags": [{"Key": "Name", "Value": config["instance_name"]}],
            }
        ],
    }

    response = ec2.run_instances(**run_params)
    instance = response["Instances"][0]
    instance_id = instance["InstanceId"]

    print(f"Instance {instance_id} is launching...")
    waiter = ec2.get_waiter("instance_running")
    waiter.wait(InstanceIds=[instance_id])

    instance = ec2.describe_instances(InstanceIds=[instance_id])["Reservations"][0]["Instances"][0]
    return {
        "instance_id": instance_id,
        "state": instance["State"]["Name"],
        "private_ip": instance.get("PrivateIpAddress"),
        "public_ip": instance.get("PublicIpAddress"),
        "availability_zone": instance["Placement"]["AvailabilityZone"],
    }


def main() -> None:
    config = load_config()

    print("Creating EC2 instance with:")
    print(f"  Region:        {config['region']}")
    print(f"  AMI:           {config['ami_id']}")
    print(f"  Type:          {config['instance_type']}")
    print(f"  Subnet:        {config['subnet_id']}")
    if config["vpc_id"]:
        print(f"  VPC:           {config['vpc_id']}")
    print(f"  Key pair:      {config['key_name']}")
    print(f"  SSM profile:   {config['iam_instance_profile']}")
    print(f"  Public IP:     {config['associate_public_ip']}")
    print(f"  Name tag:      {config['instance_name']}")
    print()

    try:
        result = create_ec2_instance(config)
    except ClientError as exc:
        print(f"AWS error: {exc.response['Error']['Message']}")
        sys.exit(1)

    print("Instance created successfully:")
    print(f"  Instance ID:   {result['instance_id']}")
    print(f"  State:         {result['state']}")
    print(f"  Private IP:    {result['private_ip']}")
    print(f"  Public IP:     {result['public_ip'] or 'N/A'}")
    print(f"  AZ:            {result['availability_zone']}")


if __name__ == "__main__":
    main()
