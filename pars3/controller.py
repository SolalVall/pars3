import click
import os
import boto3
import botocore.exceptions
import json
import pathlib
import time
import datetime
import prettytable
import json


class Controller:
    def __init__(self):
        # Allow to find home folder on all Operating Systems
        self.home_folder = str(pathlib.Path.home())
        self.aws_config_dir = ".aws-custom-location"
        self.aws_config_file = "config.creds"
        self.aws_config_location = self.home_folder + "/" + self.aws_config_dir
        self.aws_config_file_location = (
            self.aws_config_location + "/" + self.aws_config_file
        )

    def config(self):
        if os.path.isfile(self.aws_config_file_location):
            if click.confirm(
                "Do you want to override the existing config ?", default=False
            ):
                self.write_config("override")
        else:
            # Create base config folder in home dir (ensure permission)
            os.makedirs(self.aws_config_location, mode=0o700, exist_ok=True)
            self.write_config("initialize")
            # Ensure permission on conf file
            os.chmod(self.aws_config_file_location, 0o600)

        return click.Context.exit(0)

    def write_config(self, context):
        try:
            aws_id = os.environ["AWS_ACCESS_KEY_ID"]
            aws_key = os.environ["AWS_SECRET_ACCESS_KEY"]
            conf_content = (
                f"[default]\n"
                f"aws_access_key_id={aws_id}\n"
                f"aws_secret_access_key={aws_key}"
            )
            # Modify/Create base conf file
            conf_file = open(self.aws_config_file_location, "w")
            conf_file.write(conf_content)
        except KeyError:
            raise click.ClickException(
                "Environment variable required to access to AWS S3 not detected. Please export AWS_ACCESS_KEY_ID & AWS_SECRET_ACCESS_KEY"
            )
        else:
            click.echo(
                "{} Successfully {}".format(self.aws_config_file_location, context)
            )

    def load_client(self, aws_s3=False, aws_ce=False, region_name=None):
        if os.path.isfile(self.aws_config_file_location):
            os.environ["AWS_CONFIG_FILE"] = self.aws_config_file_location
            if aws_s3:
                if region_name:
                    self.s3_client = boto3.client("s3", region_name=region_name)
                else:
                    self.s3_client = boto3.client("s3")
                self.s3_resource = boto3.resource("s3")
            if aws_ce:
                self.s3_cost = boto3.client("ce")
        else:
            raise click.ClickException(
                "Please first setup your config file via the config command."
            )

    def buckets(self, **kwargs):
        bucket_result = prettytable.PrettyTable(
            [
                "Bucket Name",
                "Region",
                "Creation Date",
                "Number of files",
                "Last Modified file",
                "Total Files Size",
            ]
        )
        retrieved_data = []

        try:
            if kwargs["bucket_name"]:
                bucket_response = self.s3_client.list_objects_v2(
                    Bucket=kwargs["bucket_name"]
                )
                retrieved_data.append(
                    self.retrieve_bucket_datas(bucket_response, kwargs)
                )
            else:
                # When no bucket provided find all buckets available
                for bucket in self.s3_client.list_buckets()["Buckets"]:

                    buckets_response = self.s3_client.list_objects_v2(
                        Bucket=bucket["Name"]
                    )
                    buckets_region = buckets_response["ResponseMetadata"][
                        "HTTPHeaders"
                    ]["x-amz-bucket-region"]

                    # When region provided retrieve all buckets for that specific region
                    if kwargs["region_name"]:
                        if kwargs["region_name"] == buckets_region:
                            retrieved_data.append(
                                self.retrieve_bucket_datas(buckets_response, kwargs)
                            )
                    else:
                        retrieved_data.append(
                            self.retrieve_bucket_datas(buckets_response, kwargs)
                        )

            for row in retrieved_data:
                bucket_result.add_row(row)

        except botocore.exceptions.ClientError:
            raise click.ClickException(
                'Unable to find bucket named "{}"'.format(bucket_name)
            )
        except botocore.exceptions.EndpointConnectionError:
            raise click.ClickException(
                "Unable to find region named {}".format(region_name)
            )
        else:
            return click.echo(bucket_result)

    def retrieve_bucket_datas(self, bucket_client_response, user_filter):
        bucket_files_size = []
        bucket_timestamps = set()
        bucket_files_number = 0

        # Get base infos
        bucket_name = (
            user_filter["bucket_name"]
            if user_filter["bucket_name"]
            else bucket_client_response["Name"]
        )
        bucket_region = (
            user_filter["region_name"]
            if user_filter["region_name"]
            else bucket_client_response["ResponseMetadata"]["HTTPHeaders"][
                "x-amz-bucket-region"
            ]
        )
        resource = self.s3_resource.Bucket(bucket_name)
        bucket_creation_date = resource.creation_date
        bucket_contents = bucket_client_response["Contents"]

        # Retrive size/timestamp for each files
        for bucket_file in bucket_contents:
            #  content type (if user provided the --storage option)
            if user_filter["storage_type"]:
                if user_filter["storage_type"] == bucket_file["StorageClass"]:
                    bucket_files_size.append(int(bucket_file["Size"]))
                    bucket_timestamps.add(bucket_file["LastModified"].timestamp())
                    bucket_files_number += 1
            else:
                bucket_files_size.append(int(bucket_file["Size"]))
                bucket_timestamps.add(bucket_file["LastModified"].timestamp())
                bucket_files_number += 1

        # If timestamp and file size found we need to convert them
        if bucket_timestamps and bucket_files_size:
            # Convert timestamp
            bucket_last_modified_timestamp = max(bucket_timestamps)
            bucket_last_modified = datetime.datetime.fromtimestamp(
                bucket_last_modified_timestamp
            )

            # Convert size (if user provided the --size option)
            bucket_size = sum(bucket_files_size)
            if user_filter["size_type"]:
                default_size = {"Gb": 3, "Mb": 2, "Kb": 1}
                for key, value in default_size.items():
                    if user_filter["size_type"] == key:
                        bucket_size = "{} {}".format(
                            round((bucket_size / pow(1024, value)), 2), key
                        )
            else:
                bucket_size = "{} Bytes".format(bucket_size)
        else:
            bucket_last_modified = "N/A"
            bucket_size = "N/A"

        bucket_data = [
            bucket_name,
            bucket_region,
            bucket_creation_date,
            bucket_files_number,
            bucket_last_modified,
            bucket_size,
        ]

        return bucket_data

    def costs(self, time_interval, region_name=None):
        costs_results = prettytable.PrettyTable(
            ["Region", "Total Amount", f"Last {time_interval} days"]
        )

        # Retrieve today date in a format supported by boto3
        # And do the same for 'time_interval' days before
        today_date = datetime.date.today()
        old_date = today_date - datetime.timedelta(days=time_interval)

        try:
            # Submit price request (Filter only s3 service)
            # I was unable to find the REGION 'Values' for global query..
            if region_name:
                ce_pricing_response = self.s3_cost.get_cost_and_usage(
                    TimePeriod={"Start": str(old_date), "End": str(today_date)},
                    Granularity="DAILY",
                    Metrics=["BlendedCost"],
                    Filter={
                        "Dimensions": {
                            "Key": "SERVICE",
                            "Values": ["Amazon Simple Storage Service"],
                        },
                        "Dimensions": {"Key": "REGION", "Values": [region_name]},
                    },
                    GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
                )
            else:
                ce_pricing_response = self.s3_cost.get_cost_and_usage(
                    TimePeriod={"Start": str(old_date), "End": str(today_date)},
                    Granularity="DAILY",
                    Metrics=["BlendedCost"],
                    Filter={
                        "Dimensions": {
                            "Key": "SERVICE",
                            "Values": ["Amazon Simple Storage Service"],
                        }
                    },
                    GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
                )
                region_name = "Global"

            total_amount, daily_cost = self.retrieve_costs_data(ce_pricing_response)

            costs_results.add_row([region_name, total_amount, daily_cost])
        except:
            raise click.ClickException(
                "Unable to find cost for {} region".format(region_name)
            )
        else:
            return click.echo(costs_results)

    def retrieve_costs_data(self, ce_pricing):
        pricing_amounts = []
        daily_cost = ""

        for period in ce_pricing["ResultsByTime"]:
            period_date = period["TimePeriod"]["Start"]
            # If no groups found for the period it means price = 0
            if period["Groups"]:
                period_price = period["Groups"][0]["Metrics"]["BlendedCost"]["Amount"]
                period_unit = period["Groups"][0]["Metrics"]["BlendedCost"]["Unit"]
                daily_cost += f"[{period_date}] {period_price} {period_unit}\n"
                pricing_amounts.append(float(period_price))
            else:
                daily_cost += f"[{period_date}] 0 USD\n"

        total_amount = sum(pricing_amounts) if pricing_amounts else 0

        return [total_amount, daily_cost]

    def load(self, bucket, obj):
        # Retrieve all files in the dir provided (obj)
        obj_files = os.listdir(obj)
        for file_obj in obj_files:
            self.s3_resource.meta.client.upload_file(
                "{}/{}".format(obj, file_obj), bucket, file_obj
            )
