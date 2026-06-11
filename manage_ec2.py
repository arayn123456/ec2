#!/usr/bin/env python3
"""Start, stop, or terminate an EC2 instance using ID from data/ec2-instanceid.txt."""

import os
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

DATA_DIR = Path(__file__).parent / "data"
INSTANCE_ID_FILE = DATA_DIR / "ec2-instanceid.txt"


def load_env() -> str:
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

    return os.getenv("AWS_REGION")


def read_instance_id() -> str:
    if not INSTANCE_ID_FILE.exists():
        print(f"Error: instance ID file not found at {INSTANCE_ID_FILE}")
        print("Run get_instance_id.py first to save the instance ID.")
        sys.exit(1)

    instance_id = INSTANCE_ID_FILE.read_text(encoding="utf-8").strip()
    if not instance_id:
        print(f"Error: {INSTANCE_ID_FILE} is empty.")
        sys.exit(1)

    return instance_id


def get_ec2_client(region: str):
    return boto3.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=region,
    ).client("ec2")


def get_instance_state(ec2, instance_id: str) -> str:
    response = ec2.describe_instances(InstanceIds=[instance_id])
    return response["Reservations"][0]["Instances"][0]["State"]["Name"]


def start_instance(ec2, instance_id: str) -> None:
    state = get_instance_state(ec2, instance_id)
    if state == "running":
        print(f"Instance {instance_id} is already running.")
        return
    if state == "terminated":
        print(f"Error: instance {instance_id} is terminated and cannot be started.")
        sys.exit(1)

    print(f"Starting instance {instance_id}...")
    ec2.start_instances(InstanceIds=[instance_id])
    waiter = ec2.get_waiter("instance_running")
    waiter.wait(InstanceIds=[instance_id])
    print(f"Instance {instance_id} is now running.")


def stop_instance(ec2, instance_id: str) -> None:
    state = get_instance_state(ec2, instance_id)
    if state == "stopped":
        print(f"Instance {instance_id} is already stopped.")
        return
    if state == "terminated":
        print(f"Error: instance {instance_id} is terminated and cannot be stopped.")
        sys.exit(1)

    print(f"Stopping instance {instance_id}...")
    ec2.stop_instances(InstanceIds=[instance_id])
    waiter = ec2.get_waiter("instance_stopped")
    waiter.wait(InstanceIds=[instance_id])
    print(f"Instance {instance_id} is now stopped.")


def terminate_instance(ec2, instance_id: str) -> None:
    state = get_instance_state(ec2, instance_id)
    if state == "terminated":
        print(f"Instance {instance_id} is already terminated.")
        return

    confirm = input(f"Terminate instance {instance_id}? This cannot be undone (yes/no): ")
    if confirm.strip().lower() != "yes":
        print("Termination cancelled.")
        return

    print(f"Terminating instance {instance_id}...")
    ec2.terminate_instances(InstanceIds=[instance_id])
    waiter = ec2.get_waiter("instance_terminated")
    waiter.wait(InstanceIds=[instance_id])
    print(f"Instance {instance_id} has been terminated.")


def show_menu() -> None:
    print()
    print("EC2 Instance Manager")
    print("--------------------")
    print("1. Start instance")
    print("2. Stop instance")
    print("3. Terminate instance")
    print("0. Exit")
    print()


def main() -> None:
    region = load_env()
    instance_id = read_instance_id()
    ec2 = get_ec2_client(region)

    try:
        state = get_instance_state(ec2, instance_id)
    except ClientError as exc:
        print(f"AWS error: {exc.response['Error']['Message']}")
        sys.exit(1)

    print(f"Instance ID: {instance_id}")
    print(f"Region:      {region}")
    print(f"State:       {state}")

    show_menu()
    choice = input("Select an option: ").strip()

    actions = {
        "1": start_instance,
        "2": stop_instance,
        "3": terminate_instance,
        "0": lambda _ec2, _id: print("Exiting."),
    }

    action = actions.get(choice)
    if not action:
        print("Invalid option. Please run the script again and choose 1, 2, 3, or 0.")
        sys.exit(1)

    try:
        action(ec2, instance_id)
    except ClientError as exc:
        print(f"AWS error: {exc.response['Error']['Message']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
