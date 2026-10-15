output "s3_bucket_name" {
  description = "Nombre del bucket S3 para almacenamiento documental"
  value       = aws_s3_bucket.documents.id
}

output "s3_bucket_arn" {
  description = "ARN del bucket S3"
  value       = aws_s3_bucket.documents.arn
}

output "dynamodb_table_name" {
  description = "Nombre de la tabla DynamoDB para trazabilidad de historial"
  value       = aws_dynamodb_table.history.name
}

output "dynamodb_table_arn" {
  description = "ARN de la tabla DynamoDB"
  value       = aws_dynamodb_table.history.arn
}

output "public_api_endpoint" {
  description = "URL pública HTTPS del backend FastAPI serverless en AWS API Gateway y Lambda"
  value       = aws_apigatewayv2_api.http_api.api_endpoint
}

output "cloudwatch_log_group" {
  description = "Grupo de logs de CloudWatch para observabilidad"
  value       = aws_cloudwatch_log_group.app_logs.name
}

