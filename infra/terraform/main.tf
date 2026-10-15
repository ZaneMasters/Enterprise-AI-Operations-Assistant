terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.app_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "Operations-AI"
    }
  }
}

# 1. Bucket S3 para almacenamiento documental seguro (Principio V y VI)
resource "aws_s3_bucket" "documents" {
  bucket_prefix = "rag-docs-${var.environment}-"
  force_destroy = false
}

resource "aws_s3_bucket_versioning" "documents_versioning" {
  bucket = aws_s3_bucket.documents.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "documents_encryption" {
  bucket = aws_s3_bucket.documents.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "documents_block" {
  bucket                  = aws_s3_bucket.documents.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# 2. Tabla DynamoDB para persistencia de auditoría e historial (Principio VIII)
resource "aws_dynamodb_table" "history" {
  name         = "${var.app_name}-history-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "interaction_id"
  range_key    = "timestamp"

  attribute {
    name = "interaction_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }
}

# 3. CloudWatch Log Group para observabilidad estructurada (Principio VIII)
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/aws/ecs/${var.app_name}-${var.environment}"
  retention_in_days = 30
}

# 4. Roles y Políticas IAM con principio de menor privilegio (Principio V)
resource "aws_iam_role" "ecs_execution_role" {
  name = "${var.app_name}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_attach" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task_role" {
  name = "${var.app_name}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# Política específica de permisos mínimos para DynamoDB y S3
resource "aws_iam_policy" "task_permissions" {
  name = "${var.app_name}-task-permissions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = aws_dynamodb_table.history.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.documents.arn,
          "${aws_s3_bucket.documents.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_attach" {
  role       = aws_iam_role.ecs_task_role.name
  policy_arn = aws_iam_policy.task_permissions.arn
}

# 4.1 Permiso para que Lambda asuma el rol
resource "aws_iam_role" "lambda_role" {
  name = "${var.app_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_task_attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.task_permissions.arn
}

# 5. Función AWS Lambda Serverless para la API FastAPI
resource "aws_lambda_function" "api" {
  filename         = "${path.module}/../../lambda_function.zip"
  function_name    = "${var.app_name}-api-${var.environment}"
  role             = aws_iam_role.lambda_role.arn
  handler          = "app.main.handler"
  runtime          = "python3.12"
  timeout          = 60
  memory_size      = 512
  source_code_hash = filebase64sha256("${path.module}/../../lambda_function.zip")

  environment {
    variables = {
      ENVIRONMENT         = var.environment
      LLM_PROVIDER        = "bedrock"
      BEDROCK_MODEL_ID    = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
      BEDROCK_REGION      = var.aws_region
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.history.name
      S3_BUCKET_NAME      = aws_s3_bucket.documents.id
    }
  }
}

# 6. HTTP API Gateway Serverless (Cero costo fijo, pago por petición)
resource "aws_apigatewayv2_api" "http_api" {
  name          = "${var.app_name}-api-${var.environment}"
  protocol_type = "HTTP"
  target        = aws_lambda_function.api.arn

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["*"]
    allow_headers = ["*"]
    max_age       = 86400
  }
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*"
}


