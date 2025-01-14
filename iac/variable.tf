variable "bucket_name" {
  type        = string
  default     = "airbyte-motherduck-hackathon"
  description = "The name of the bucket to be used for this project"
}

variable "aws_region" {
  type        = string
  default     = "eu-west-2"
  description = "Your region for the bucket"
}

variable "aws_secret_access_key" {
  type        = string
  description = "Your AWS secret key"
}


variable "aws_access_key_id" {
  type        = string
  description = "Your AWS secret key id"
}


variable "airbyte_workspace_id" {
  type        = string
  description = "Your Airbyte workspace ID"
}

variable "client_id" {
  type        = string
  description = "Your airbyte client id"
}

variable "client_secret" {
  type        = string
  description = "Your airbyte client secret"
}

variable "motherduck_api_key" {
  type        = string
  description = "Your motherduck API key"
}
