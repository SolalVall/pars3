provider "aws" {
  region  = var.region_name
  shared_credentials_file = "~/.aws-custom-location/config.creds"
  profile = "default"
}
