terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0.1"
    }
    airbyte = {
      source = "airbytehq/airbyte"
      version = "0.6.5"
    }
  }
}

provider "aws" {
  region = var.aws_region
}
provider "docker" {}

provider "airbyte" {
  client_id = var.client_id
  client_secret = var.client_secret
}
resource "random_id" "airbyte_id" {
  byte_length = 8
}
resource "aws_s3_bucket" "s3_bucket" {
  bucket = var.bucket_name
  tags = {
    Name        = var.bucket_name
    Environment = "dev"
    Purpose     = "Hackathon"
  }
}

resource "docker_image" "airbyte_hackathon" {
  name = "airbyte_motherduck_hackathon:latest"

  build {
    context    = ".."
    dockerfile = "../Dockerfile.app"
  }
  depends_on = [aws_s3_bucket.s3_bucket]
}


resource "docker_container" "airbyte-hackathon" {
  name  = "airbyte-motherduck-container"
  image = docker_image.airbyte_hackathon.name
  ports {
    internal = 8501
    external = 8501
  }
  rm = true

}

resource "airbyte_source_s3" "aribyte_source_s3" {
  configuration = {
    aws_access_key_id     = "${var.aws_access_key_id}"
    aws_secret_access_key = "${var.aws_secret_access_key}"
    bucket                = aws_s3_bucket.s3_bucket.id
    region_name           = var.aws_region
    streams = [
      {
        days_to_sync_if_history_is_full = 3
        format = {
          jsonl_format = {
            double_as_string = true
          }
        }
        globs = [
          "output/brand=*/model_number=*/sections/*.json",
        ]
        name                                        = "manual_sections"
        recent_n_files_to_read_for_schema_discovery = 3
        schemaless                                  = true
        validation_policy                           = "Emit Record"
      },
    ]
  }
  name          = "Airbyte-motherduck-s3-${random_id.airbyte_id.hex}"
  workspace_id  = var.airbyte_workspace_id
}
