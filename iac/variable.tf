variable "bucket_name" {
   type = string
   default = "airbyte-motherduck-hackathon-1"
   description = "The name of the bucket for this project"
}

variable "aws_region" {
   type = string
   default = "eu-west-2"
   description = "The region for the bucket"
}
