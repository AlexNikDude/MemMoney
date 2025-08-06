variable "telegram_token" {}
variable "db_password" {}
variable "aws_region" {}
variable "account_id" {}
variable "repo_name" {}

# Database configuration variables
variable "db_name" {
  description = "Database name"
  type        = string
  default     = "memmoneydb"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "postgres"
}

variable "db_port" {
  description = "Database port"
  type        = number
  default     = 5432
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Initial allocated storage in GB"
  type        = number
  default     = 20
}
