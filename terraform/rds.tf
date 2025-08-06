resource "aws_db_subnet_group" "default" {
  name       = "memmoney-bot-db-subnet-group"
  subnet_ids = [aws_subnet.subnet1.id, aws_subnet.subnet2.id]
}

resource "aws_db_instance" "postgres" {
  identifier              = "memmoney-bot-db"
  engine                  = "postgres"
  engine_version          = "17.5"
  instance_class          = var.db_instance_class
  allocated_storage       = var.db_allocated_storage
  storage_type            = "gp2"
  storage_encrypted       = true
  publicly_accessible     = true
  
  db_name                 = var.db_name
  username                = var.db_username
  password                = var.db_password
  
  port                    = var.db_port
  
  vpc_security_group_ids  = [aws_security_group.rds_sg.id]
  db_subnet_group_name    = aws_db_subnet_group.default.name
  
  tags = {
    Name = "memmoney-bot-database"
    Environment = "production"
  }
}
