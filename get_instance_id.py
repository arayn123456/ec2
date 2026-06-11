#!/usr/bin/env python3
"""Find a running EC2 instance and save its ID to data/ec2-instanceid.txt."""

import os
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_FILE = DATA_DIR / "ec2-instanceid.txt"


def load_env() -> dict:
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print(f"Error: .env file not found at {env_path}")
        sys.exit(1)

    load_dotenv(env_path)

    required = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        print(f"Error: missing required .env variables: {', '.join(missing)}")
        sys.exit(1)

    return {
        "region": os.getenv("AWS_REGION"),
        "instance_name": os.getenv("INSTANCE_NAME", "ec2-instance"),
    }


def get_running_instance_id(config: dict) -> str:
    session = boto3.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=config["region"],
    )
    ec2 = session.client("ec2")

    response = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Name", "Values": [config["instance_name"]]},
            {"Name": "instance-state-name", "Values": ["running"]},
        ]
    )

    instances = []
    for reservation in response["Reservations"]:
        instances.extend(reservation["Instances"])

    if not instances:
        print(
            f"Error: no running instance found with Name tag '{config['instance_name']}'"
        )
        sys.exit(1)

    instances.sort(key=lambda i: i["LaunchTime"], reverse=True)
    return instances[0]["InstanceId"]


def save_instance_id(instance_id: str) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(f"{instance_id}\n", encoding="utf-8")
    return OUTPUT_FILE


def main() -> None:
    config = load_env()

    print(f"Looking for running instance: {config['instance_name']}")
    print(f"Region: {config['region']}")
    print()

    try:
        instance_id = get_running_instance_id(config)
        output_path = save_instance_id(instance_id)
    except ClientError as exc:
        print(f"AWS error: {exc.response['Error']['Message']}")
        sys.exit(1)

    print(f"Instance ID: {instance_id}")
    print(f"Saved to:    {output_path}")


if __name__ == "__main__":
    main()
