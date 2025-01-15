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
      source  = "airbytehq/airbyte"
      version = "0.6.5"
    }
  }
}

provider "aws" {
  region = var.aws_region
}
provider "docker" {}

provider "airbyte" {
  client_id     = var.client_id
  client_secret = var.client_secret
}

locals {
  env_file_content = file("../.env")
}
resource "random_id" "unique_id" {
  byte_length = 4
}
resource "aws_s3_bucket" "s3_bucket" {
  bucket = var.bucket_name
  tags = {
    Name        = var.bucket_name
    Environment = "dev"
    Purpose     = "Hackathon"
  }
  lifecycle {
    prevent_destroy = false
  }
}

resource "docker_image" "airbyte_hackathon" {
  name = "airbyte_motherduck_hackathon:${random_id.unique_id.id}"

  build {
    context    = ".."
    dockerfile = "../Dockerfile.app"
  }
  depends_on = [aws_s3_bucket.s3_bucket]

}


resource "docker_container" "airbyte-hackathon" {
  name  = "airbyte-motherduck-container"
  image = "${docker_image.airbyte_hackathon.name}"
  ports {
    internal = 8501
    external = 8501
  }
  rm = true

}

resource "airbyte_source_s3" "source_s3" {
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
        recent_n_files_to_read_for_schema_discovery = 5
        schemaless                                  = true
        validation_policy                           = "Emit Record"
        schemaless = false
      },
    ]
  }
  name         = "airbyte_s3_src_${random_id.unique_id.hex}"
  workspace_id = var.airbyte_workspace_id
}


resource "airbyte_destination_duckdb" "destination_duckdb" {
  configuration = {
    destination_path   = "md:"
    motherduck_api_key = "${var.motherduck_api_key}"
    schema             = "main"
  }
  name         = "airbyte_motherduck_destination_${random_id.unique_id.hex}"
  workspace_id = var.airbyte_workspace_id
  depends_on   = [airbyte_source_s3.source_s3]
}


resource "airbyte_connection" "s3-airbyte-motherduck-connection" {
  data_residency                       = "eu"
  destination_id                       = airbyte_destination_duckdb.destination_duckdb.destination_id
  name                                 = "air_md_dync"
  namespace_definition                 = "destination"
  non_breaking_schema_updates_behavior = "propagate_columns"
  prefix                               = "hackathon_"
  source_id                            = airbyte_source_s3.source_s3.source_id
  status                               = "active"
}

resource "airbyte_source_airtable" "source_airtable" {
  configuration = {
    credentials = {
      personal_access_token = {
        api_key = "${var.airtable_pat}"
      }
    }
  }
  name         = "crm_source_airtable"
  workspace_id = var.airbyte_workspace_id
}

resource "airbyte_connection" "airtable-airbyte-motherduck-connection" {
  data_residency                       = "eu"
  destination_id                       = airbyte_destination_duckdb.destination_duckdb.destination_id
  name                                 = "airtable_sync"
  namespace_definition                 = "destination"
  non_breaking_schema_updates_behavior = "propagate_columns"
  prefix                               = "hackathon_"
  source_id                            = airbyte_source_airtable.source_airtable.source_id
  status                               = "active"
}
