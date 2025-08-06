output "db_endpoint" {
  description = "The connection endpoint for the RDS instance"
  value       = aws_db_instance.postgres.endpoint
}

output "db_port" {
  description = "The port on which the DB accepts connections"
  value       = aws_db_instance.postgres.port
}

output "db_name" {
  description = "The name of the database"
  value       = aws_db_instance.postgres.db_name
}

output "db_username" {
  description = "The master username for the database"
  value       = aws_db_instance.postgres.username
}

output "db_password" {
  description = "The master password for the database"
  value       = aws_db_instance.postgres.password
  sensitive   = true
}

output "db_connection_string" {
  description = "The database connection string"
  value       = "postgresql://${aws_db_instance.postgres.username}:${aws_db_instance.postgres.password}@${aws_db_instance.postgres.endpoint}:${aws_db_instance.postgres.port}/${aws_db_instance.postgres.db_name}"
  sensitive   = true
} 