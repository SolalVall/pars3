import click
from pars3.controller import Controller


@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj = Controller()
    """
    Command line to retrieve s3 datas
    \b
    """
    pass


@click.command()
@click.pass_context
def config(ctx):
    """
    Setup aws login access
    \b
    """
    ctx.obj.config()


@click.command()
@click.option("--name", "bucket_name", help="Filter by bucket name")
@click.option("--region", "region_name", help="Filter by AWS region")
@click.option(
    "--size",
    "size_type",
    type=click.Choice(["Gb", "Mb", "Kb"]),
    help="Display bucket size in specific format",
)
@click.option(
    "--storage",
    "storage_type",
    type=click.Choice(["STANDARD", "RR", "IA"]),
    help="Display bucket data based on storage type",
)
@click.pass_context
def bucket(ctx, bucket_name, region_name, size_type, storage_type):
    """
    Retrive s3 bucket informations
    \b
    """
    ctx.obj.load_client(aws_s3=True, region_name=region_name)
    if bucket_name and region_name:
        raise click.ClickException(
            "region and name options can't be used at the same time"
        )
    else:
        ctx.obj.buckets(
            bucket_name=bucket_name,
            region_name=region_name,
            size_type=size_type,
            storage_type=storage_type,
        )


@click.command()
@click.option("--days", "days_interval", type=int, default=3)
@click.option("--region", "region_name")
@click.pass_context
def cost(ctx, region_name, days_interval):
    """
    Retrive s3 cost informations
    \b
    """
    if days_interval > 7 or days_interval < 1:
        raise click.ClickException("Time interval should be 1 to 7 days")
    else:
        ctx.obj.load_client(aws_ce=True)
        ctx.obj.costs(days_interval, region_name)


@click.command()
@click.option("--bucket", "bucket_name", required=True)
@click.option("--object", "object_path", required=True)
@click.pass_context
def load(ctx, bucket_name, object_path):
    """
    Load s3 bucket content (for testing purpose)
    \b
    """
    ctx.obj.load_client(aws_s3=True)
    ctx.obj.load(bucket_name, object_path)


def main():
    cli.add_command(config)
    cli.add_command(bucket)
    cli.add_command(cost)
    cli.add_command(load)
    cli()


if __name__ == "__main__":
    main()
