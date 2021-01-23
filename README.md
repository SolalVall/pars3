# pars3

A python CLI to retrieve s3 datas

## Requirements

- An AWS account
- AWS credentials for your IAM user
- AWS policies linked to your IAM user:
  - s3 default policy: `AmazonS3FullAccess`
  - Cost Explorer custom policy (IAM -> Strategies -> Creer une strategie -> JSON -> Copy paste the following)

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": "ce:*",
        }
    ]
}
```
- Python >= 3.6
- Pip

## Setup

Clone the project and Install the CLI:

```
git clone https://github.com/SolalVall/pars3.git
cd pars3
pip install .
```

Configure your AWS creds to work with `pars3`

```bash
# First you need to set your credentials as environment vars
# There will be pick up automatically via `pars3 config` and injected in a custom secured location
export AWS_ACCESS_KEY_ID="***********"
export AWS_SECRET_ACCESS_KEY="********"

pars3 config
```

## Features

### config

**Command**

`pars3 config`

**Details**

Setup an AWS credentials file required by other pars3 commands in a custom location ($HONE/.aws-custom-location/config.creds)

Benefits:
- Allow to login automatically in AWS when using pars3 commands
- Avoid override of an existing `~/.aws/config`
- Secure:
  - 700 perms applied on .aws-config-location dir
  - 600 perms applied on config.creds file

### bucket

**Command**

`pars3 bucket [OPTIONS]`

**Details**

Allow to parse s3 bucket data. Multiple filter can be provided via CLI options.

**Options**

`--name bucket_name`       Display data for a specific bucket
`--region region_name`     Display buckets data for a specific region
`--size size_type`         Display bucekt total file size in a desired format (Choice: [Gb|Mb|Kb])
`--storage storage_type`   Filter bucket data based on storage type (Choice: [STANDARD|RR|IA)

**Examples**

```bash
# Retrieve data for 'test-bucket' only
# Total files size will be in 'Gb' format
pars3 --name test-bucket --size Gb

# Apply search on all buckets located in 'us-east-1'
# Results would be based only on 'STANDARD' file type (other type are omitted)
pars3 --region us-east-1 --storage STANDARD

# Apply search on all buckets located in 'us-east-1'
# Total files size will be in 'Mb' format
# Results would be based only on 'RR' file type (other type are omitted)
pars3 --region us-east-1 --size Mb --storage RR
```

*Notes: region and name options can't be executed at the same time*

### cost


**Command**

`pars3 cost [OPTIONS]`

**Details**

Retrieve cost informations related to s3 services

**Options**

`--region region_name`   Display s3 costs for a specific region
`--days day_interval`    Specify start date (in days) for cost retrieval (Default is 3 days. Max is 7 days)

**Examples**

```bash
# Retrieve s3 costs for 'ca-central-1' region
pars3 cost --region ca-central-1

# Retrieve last 6 days costs for 'ca-central-1' region
pars3 cost --region ca-central-1 --days 6
```

### load

**Command**

`pars3 load [OPTIONS]`

**Details**

Insert s3 object into specific bucket.

**Options**

`--bucket bucket_name`   Specify in which bucket object should be sotred (Required)
`--object folder_path`   Specify a local folder containing the object to store (Required)

**Examples**

```bash
# Inject all the files contains in the object path into 'test-solal' bucket
pars3 load --bucket test-solal --object /path/to/a/folder/containing/lot/of/files
```

*Notes: This command is used for testing purpose. It allows me to generate load in my AWS s3. Check tests folder main script*

## Live Demo & Tests

*Required Terraform >= 0.14*

### Tests

run_tests is a custom bash script which allows to easily create and populate AWS s3 buckets. Thanks to that process I can at the same time generate loads in my AWS s3 account and test pars3 CLI against the newly created buckets.

**How to test**

```bash
# To run the test, please ensure that you've followed the [`Setup`](#Setup) section
cd tests
./run_tests --bucket-number 1 --files-nuber 999
```

**Details**

The above command will execute the following actions:
- Create 1 local directory named:
  - object-folder-1
- Populate the above folder with random file size (from 1 to 1.1Mo):
  - 999 files in object-folder-1/
- Create 3 buckets in AWS by using Terraform and your `~/aws-config-location/config.creds` (generated via `pars3 config`)
- Populate bucket with the according folder
- Run some `pars3` commands
- Clean the local folder

### Live Demo
