variable "bucket_name" {
  type        = string
  default     = "airbyte-motherduck-hackathon-1"
  description = "Default name of the bucket for this project"
}

variable "aws_region" {
  type        = string
  default     = "eu-west-2"
  description = "The region for the bucket"
}

variable "aws_secret_access_key" {
  type        = string
  description = "The AWS secret key"
}


variable "aws_access_key_id" {
  type        = string
  description = "The AWS secret key id"
}


variable "airbyte_workspace_id" {
  type        = string
  description = "The Airbyte workspace ID"
}

variable "client_id" {
  type        = string
  description = "The airbyte client id"
}

variable "client_secret" {
  type        = string
  description = "The airbyte client secret"
}
