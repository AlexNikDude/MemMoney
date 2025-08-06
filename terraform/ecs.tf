# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "memmoney-bot-cluster"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
  
  tags = {
    Name = "memmoney-bot-cluster"
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "bot" {
  family                   = "memmoney-bot"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "memmoney-bot"
      image = "${var.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.repo_name}:latest"
      
      portMappings = [
        {
          containerPort = 80
          protocol      = "tcp"
        }
      ]
      
      environment = [
        {
          name  = "TELEGRAM_BOT_TOKEN"
          value = var.telegram_token
        },
        {
          name  = "POSTGRES_HOST"
          value = aws_db_instance.postgres.endpoint
        },
        {
          name  = "POSTGRES_PORT"
          value = tostring(aws_db_instance.postgres.port)
        },
        {
          name  = "POSTGRES_DB"
          value = aws_db_instance.postgres.db_name
        },
        {
          name  = "POSTGRES_USER"
          value = aws_db_instance.postgres.username
        },
        {
          name  = "POSTGRES_PASSWORD"
          value = aws_db_instance.postgres.password
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.bot_logs.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
  
  tags = {
    Name = "memmoney-bot-task-definition"
  }
}

# ECS Service
resource "aws_ecs_service" "bot" {
  name            = "memmoney-bot-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.bot.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets          = [aws_subnet.subnet1.id, aws_subnet.subnet2.id]
    security_groups  = [aws_security_group.ecs_sg.id]
    assign_public_ip = true
  }
  
  depends_on = [aws_lb_listener.bot]
  
  load_balancer {
    target_group_arn = aws_lb_target_group.bot.arn
    container_name   = "memmoney-bot"
    container_port   = 80
  }
  
  tags = {
    Name = "memmoney-bot-service"
  }
}

# Application Load Balancer
resource "aws_lb" "bot" {
  name               = "memmoney-bot-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = [aws_subnet.subnet1.id, aws_subnet.subnet2.id]
  
  tags = {
    Name = "memmoney-bot-alb"
  }
}

# ALB Target Group
resource "aws_lb_target_group" "bot" {
  name        = "memmoney-bot-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }
  
  tags = {
    Name = "memmoney-bot-target-group"
  }
}

# ALB Listener
resource "aws_lb_listener" "bot" {
  load_balancer_arn = aws_lb.bot.arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.bot.arn
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "bot_logs" {
  name              = "/ecs/memmoney-bot"
  retention_in_days = 7
  
  tags = {
    Name = "memmoney-bot-logs"
  }
} 