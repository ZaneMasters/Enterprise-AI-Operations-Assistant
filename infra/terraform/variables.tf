variable "aws_region" {
  description = "Región de AWS para desplegar la infraestructura"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Ambiente de despliegue (production, staging, dev)"
  type        = string
  default     = "production"
}

variable "app_name" {
  description = "Nombre identificador del asistente y sus recursos asociados"
  type        = string
  default     = "enterprise-ai-assistant"
}

variable "container_port" {
  description = "Puerto en el que escucha el servicio FastAPI"
  type        = number
  default     = 8000
}

variable "task_cpu" {
  description = "CPU asignada a la tarea ECS Fargate (256, 512, 1024)"
  type        = string
  default     = "512"
}

variable "task_memory" {
  description = "Memoria RAM asignada a la tarea ECS Fargate (1024, 2048)"
  type        = string
  default     = "1024"
}
