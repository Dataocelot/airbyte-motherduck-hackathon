terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Configure the AWS Provider
provider "aws" {
  region = var.aws_region
}

resource "aws_s3_bucket" "s3_bucket" {
  bucket = var.bucket_name
    tags = {
      Name        = var.bucket_name
      Environment = "Production"
      Purpose = "Hackathon"
    }
}
