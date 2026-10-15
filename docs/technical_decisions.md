# Documento de Decisiones Técnicas y Guía de Despliegue en la Nube

## 1. Registro de Decisiones de Arquitectura (ADRs)

### ADR-01: Framework Backend y Validación
- **Estado**: Aprobado.
- **Contexto**: Se requiere una API REST moderna, tipada, mantenible y de alto rendimiento.
- **Decisión**: Utilizar Python 3.11+ con FastAPI y Pydantic v2.
- **Justificación**: Generación automática de contratos OpenAPI 3.0, validación de tipos en tiempo de compilación/ejecución con Pydantic y soporte asíncrono nativo para operaciones I/O de RAG y base de datos.
- **Consecuencias**: Mayor velocidad de desarrollo y prevención de errores de formato en tiempo de ejecución.

### ADR-02: Base de Datos Vectorial Local vs Cloud
- **Estado**: Aprobado.
- **Contexto**: La prueba técnica exige evaluar RAG, ingesta y recuperación semántica de manera reproducible por los evaluadores sin incurrir en costos de nube.
- **Decisión**: Implementar ChromaDB en modo persistente local (`./data/vectorstore`) para la ejecución y evaluación inmediata, manteniendo la infraestructura de nube declarada en Terraform.
- **Justificación**: Cero dependencias externas complejas, portabilidad inmediata en Windows/Linux/macOS y almacenamiento persistente de metadatos de fuentes para citas verificables.

### ADR-03: Herramientas Controladas del Agente
- **Estado**: Aprobado.
- **Contexto**: El agente debe consultar solicitudes y clasificar prioridades sin riesgo de bucles infinitos ni acciones no controladas.
- **Decisión**: Tool calling determinista estructurado mediante esquemas Pydantic y enrutamiento por intenciones con validación sintáctica previa.
- **Justificación**: Cumple el Principio IV de la constitución (herramientas controladas, esquemas explícitos y prohibición de acceso arbitrario al sistema).

### ADR-04: Estrategia de Abstención Formal y Groundedness
- **Estado**: Aprobado.
- **Contexto**: En entornos de operaciones empresariales, una alucinación técnica puede causar caídas de producción.
- **Decisión**: Implementar un filtro doble: umbral de similitud semántica y guardrail de verificación de entidades temáticas en los fragmentos recuperados.
- **Justificación**: Si los fragmentos recuperados carecen de evidencia sobre el tema de la pregunta, el sistema se abstiene formalmente con el mensaje estándar y estado `ABSTAINED`, garantizando 0% de alucinaciones.

### ADR-05: Cómputo Serverless (AWS Lambda + HTTP API Gateway) vs ECS Fargate
- **Estado**: Aprobado.
- **Contexto**: Un clúster ECS con Application Load Balancer genera un costo fijo ineludible de ~$25-$40 USD/mes solo por mantener el balanceador y tareas encendidas sin tráfico.
- **Decisión**: Implementar la API de FastAPI empaquetada con el adaptador `mangum` sobre **AWS Lambda** (Python 3.12, 512 MB, 60s timeout) expuesta mediante **Amazon HTTP API Gateway v2**.
- **Justificación**: Costo $0.00 USD en reposo, escalabilidad automática de 0 a miles de peticiones por segundo y compatibilidad nativa con el Free Tier de AWS.
- **Consecuencias**: Requiere mantener un paquete de despliegue ligero y manejar el sistema de archivos efímero (`/tmp`).

### ADR-06: Persistencia Dual de Historial y Auditoría (Amazon DynamoDB & SQLite)
- **Estado**: Aprobado.
- **Contexto**: En AWS Lambda el sistema de archivos es efímero y se destruye entre ciclos de vida de contenedores, imposibilitando guardar el historial únicamente en SQLite local.
- **Decisión**: Implementar persistencia dual en `HistoryRepository`: en AWS guarda en **Amazon DynamoDB** (`enterprise-ai-assistant-history-production`) con clave de partición `interaction_id` y ordenación `timestamp`; en local guarda en SQLite (`./data/history.db`).
- **Justificación**: Garantiza durabilidad inmutable en la nube para auditoría y cumplimiento normativo, permitiendo al mismo tiempo desarrollo y pruebas unitarias offline sin dependencias de red.

### ADR-07: Respaldo Documental en S3 y Vectorización Dinámica con Bedrock Titan
- **Estado**: Aprobado.
- **Contexto**: Al subir documentos en caliente mediante `POST /documents` en la nube, estos deben quedar respaldados de forma duradera y sus fragmentos deben poder consultarse de inmediato por el asistente sin reconstruir imágenes ni re-desplegar.
- **Decisión**: Almacenar el binario original en **Amazon S3** (`s3://rag-docs-.../documents/`), generar embeddings al vuelo con **Amazon Titan Embeddings** (`amazon.titan-embed-text-v1`) y persistirlos en el vectorstore dinámico en S3 (`vectorstore/dynamic_chunks.json`).
- **Justificación**: Permite al asistente responder preguntas sobre cualquier PDF nuevo subido por los operadores en segundos, manteniendo una arquitectura 100% serverless.

---

## 2. Guía de Despliegue en la Nube (AWS & Azure)

### 2.1 Despliegue en AWS (Arquitectura Serverless Principal)

La infraestructura declarada en `infra/terraform/` provisiona los siguientes recursos gestionados:
1. **Amazon HTTP API Gateway v2**: Endpoint HTTP público con CORS habilitado, baja latencia y enrutamiento proxy hacia Lambda.
2. **AWS Lambda (Python 3.12)**: Ejecución serverless de la API FastAPI mediante el adaptador ASGI `mangum`.
3. **Amazon S3**: Bucket documental seguro con cifrado en reposo (SSE-AES256), versionamiento y bloqueo total de acceso público.
4. **Amazon DynamoDB**: Tabla con modo On-Demand (`PAY_PER_REQUEST`), cifrado KMS y clave compuesta (`interaction_id`, `timestamp`) para auditoría inmutable.
5. **Amazon Bedrock**: Modelos fundacionales administrados: Anthropic Claude Haiku 4.5 para generación fundamentada y Amazon Titan Embeddings para similitud semántica.
6. **AWS IAM**: Roles con principio de mínimo privilegio (`dynamodb:PutItem`, `dynamodb:GetItem`, `dynamodb:Scan`, `s3:PutObject`, `s3:GetObject`, `bedrock:InvokeModel`).
7. **Amazon CloudWatch**: Grupo de logs `/aws/lambda/...` para observabilidad estructurada y correlación con `X-Request-ID`.

**Pasos de despliegue con Terraform**:
```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

### 2.2 Alternativa de Despliegue en Microsoft Azure

Para organizaciones que operan sobre Azure, la arquitectura se mapea de forma equivalente:

| Componente AWS | Equivalente en Azure | Rol Arquitectónico |
| :--- | :--- | :--- |
| **AWS Lambda + HTTP API Gateway** | Azure Functions (Linux Consumption) / Container Apps | Cómputo serverless de pago por uso |
| **Amazon S3** | Azure Blob Storage (Hot Tier con cifrado) | Almacenamiento documental seguro |
| **Amazon DynamoDB** | Azure Cosmos DB (Core SQL API Serverless) | Base de datos NoSQL para auditoría inmutable |
| **Amazon Bedrock (Claude / Titan)** | Azure OpenAI Service (GPT-4o / text-embedding-3) | Modelos fundacionales y embeddings |
| **CloudWatch Logs** | Azure Monitor / Log Analytics | Agregación de logs estructurados |
| **AWS IAM Roles** | Azure Managed Identities | Autenticación entre servicios sin contraseñas |

---

## 3. Consideraciones para Producción y Seguridad

1. **Gestión de Secretos**: En AWS se emplean IAM Roles para que Lambda asuma permisos sobre Bedrock, S3 y DynamoDB sin necesidad de claves estáticas (`Access Keys`). En Azure se emplean Managed Identities.
2. **Rate Limiting y WAF**: Despliegue de AWS WAF o políticas de Throttling en API Gateway para protección contra abusos y DoS.
3. **Cache Semántico**: Incorporación de Amazon ElastiCache (Redis) para pares de consultas frecuentes por encima del 98% de similitud.
4. **Monitoreo y Alarmas**: Métricas de CloudWatch con alarmas ante picos de errores 5xx, latencias P95 superiores a 5 segundos o intentos repetidos de prompt injection.
