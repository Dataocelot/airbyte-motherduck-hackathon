variable "bucket_name" {
   type = string
   default = "airbyte-motherduck-hackathon-1"
   description = "Default name of the bucket for this project"
}

variable "aws_region" {
   type = string
   default = "eu-west-2"
   description = "The region for the bucket"
}

variable "airbyte_workspace_id" {
   type = string
   description = "Your Airbyte workspace ID"
}
