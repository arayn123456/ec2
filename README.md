# AWS EC2 Automation

Python scripts to create, manage, and track EC2 instances using configuration from a `.env` file.

## Features

- Create EC2 instances with public IP and SSM IAM instance profile
- Save running instance ID to a local file
- Start, stop, or terminate instances via an interactive menu

## Prerequisites

- Python 3.8+
- AWS account with permissions for EC2 and IAM instance profiles
- An IAM instance profile with **AmazonSSMManagedInstanceCore** (for SSM Session Manager)
- An EC2 key pair in your AWS region
- A VPC subnet (public subnet if using a public IP)

## Setup

1. Clone or download this project.

2. Create your local environment file:

   ```powershell
   copy .env.example .env
   ```

   Edit `.env` with your AWS credentials and EC2 settings.

3. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

   Optional: use a virtual environment:

   ```powershell
   python -m venv .ec2
   .\.ec2\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

   > **Important:** Never commit `.env`, `.pem` keys, or `data/ec2-instanceid.txt`. These are excluded via `.gitignore`.

## Configuration

Create a `.env` file with the following variables:

```env
# AWS credentials
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=us-east-1

# EC2 configuration
AMI_ID=ami-xxxxxxxx
INSTANCE_TYPE=t2.micro
KEY_NAME=your-key-pair-name
SUBNET_ID=subnet-xxxxxxxx
VPC_ID=vpc-xxxxxxxx

# IAM instance profile with AmazonSSMManagedInstanceCore (for SSM)
IAM_INSTANCE_PROFILE=your-ssm-instance-profile-name

# Optional: comma-separated security group IDs
SECURITY_GROUP_IDS=sg-xxxxxxxx

# Assign a public IP (true/false)
ASSOCIATE_PUBLIC_IP=true

# Optional
INSTANCE_NAME=my-ec2-instance
VOLUME_SIZE_GB=8
```

### Required variables

| Variable | Description |
|----------|-------------|
| `AWS_ACCESS_KEY_ID` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `AWS_REGION` | AWS region (e.g. `us-east-1`) |
| `AMI_ID` | Amazon Machine Image ID |
| `INSTANCE_TYPE` | Instance type (e.g. `t2.micro`) |
| `KEY_NAME` | EC2 key pair name in AWS |
| `SUBNET_ID` | Subnet to launch the instance in |
| `IAM_INSTANCE_PROFILE` | IAM instance profile for SSM access |

### Optional variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VPC_ID` | — | VPC ID (informational) |
| `SECURITY_GROUP_IDS` | — | Comma-separated security group IDs |
| `ASSOCIATE_PUBLIC_IP` | `true` | Assign a public IP at launch |
| `INSTANCE_NAME` | `ec2-instance` | Name tag for the instance |
| `VOLUME_SIZE_GB` | `8` | Root EBS volume size in GB |

## Scripts

### 1. `create_ec2.py` — Create an EC2 instance

Launches a new EC2 instance using settings from `.env`. Attaches the SSM IAM instance profile, assigns a public IP (if enabled), and waits until the instance is running.

```powershell
python create_ec2.py
```

### 2. `get_instance_id.py` — Save instance ID

Finds the running instance matching `INSTANCE_NAME` in `.env` and saves its ID to `data/ec2-instanceid.txt`.

```powershell
python get_instance_id.py
```

### 3. `manage_ec2.py` — Start, stop, or terminate

Reads the instance ID from `data/ec2-instanceid.txt` and shows an interactive menu:

```
EC2 Instance Manager
--------------------
1. Start instance
2. Stop instance
3. Terminate instance
0. Exit
```

```powershell
python manage_ec2.py
```

Terminate requires typing `yes` to confirm.

## Typical workflow

```powershell
# 1. Create the instance
python create_ec2.py

# 2. Save the instance ID locally
python get_instance_id.py

# 3. Manage the instance (start / stop / terminate)
python manage_ec2.py
```

## Project structure

```
ec2/
├── .env.example          # Environment template (safe to commit)
├── .env                  # Local config (gitignored)
├── .gitignore
├── create_ec2.py         # Create EC2 instance
├── get_instance_id.py    # Fetch and save running instance ID
├── manage_ec2.py         # Start, stop, or terminate instance
├── requirements.txt      # Python dependencies
├── data/
│   ├── .gitkeep
│   └── ec2-instanceid.txt   # Saved instance ID (generated, gitignored)
└── README.md
```

## Git

This repo is set up to exclude secrets and generated files:

| Ignored | Reason |
|---------|--------|
| `.env` | AWS credentials |
| `data/*.txt` | Runtime instance IDs |
| `data/*.pem` | SSH private keys |
| `.ec2/`, `venv/` | Virtual environments |
| `__pycache__/` | Python bytecode |

To initialize and make your first commit locally:

```powershell
git init
git add .
git status
git commit -m "Initial commit: EC2 automation scripts"
```

## SSM Session Manager

With the SSM IAM instance profile attached, you can connect without SSH:

```powershell
aws ssm start-session --target i-xxxxxxxxxxxxxxxxx
```

**SSM requirements:**

- IAM role with `AmazonSSMManagedInstanceCore` policy
- Instance profile linked to that role
- Outbound HTTPS (port 443) allowed in the security group
- SSM agent running on the AMI (included on Amazon Linux and Ubuntu AMIs)

## SSH access (optional)

If you assigned a public IP and opened port 22 in your security group:

```powershell
ssh -i your-key.pem ec2-user@<public-ip>
```

Use `ec2-user` for Amazon Linux, `ubuntu` for Ubuntu AMIs.

## Troubleshooting

| Issue | Possible fix |
|-------|----------------|
| `.env file not found` | Create `.env` in the project root |
| `instance ID file not found` | Run `get_instance_id.py` first |
| No public IP assigned | Use a public subnet and set `ASSOCIATE_PUBLIC_IP=true` |
| SSM connection fails | Verify IAM profile, security group egress, and instance is running |
| `InvalidAMIID.NotFound` | Use a valid AMI ID for your region |

## Dependencies

- [boto3](https://pypi.org/project/boto3/) — AWS SDK for Python
- [python-dotenv](https://pypi.org/project/python-dotenv/) — Load `.env` variables
