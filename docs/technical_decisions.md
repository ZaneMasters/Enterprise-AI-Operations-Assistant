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

---

## 2. Guía de Despliegue en la Nube (AWS & Azure)

### 2.1 Despliegue en AWS (Arquitectura Principal)

La infraestructura declarada en `infra/terraform/` provisiona los siguientes recursos:
1. **Amazon ECS Fargate**: Cómputo serverless para ejecutar el contenedor Docker de FastAPI sin gestión de servidores.
2. **Amazon S3**: Almacenamiento seguro de documentos con cifrado en reposo (SSE-AES256) y bloqueo total de acceso público.
3. **Amazon DynamoDB**: Tabla con modo On-Demand (`PAY_PER_REQUEST`) y clave primaria compuesta (`interaction_id`, `timestamp`) para trazabilidad de auditoría.
4. **AWS IAM**: Roles con principio de mínimo privilegio para la tarea ECS, limitando accesos únicamente a las operaciones requeridas.
5. **Amazon CloudWatch**: Grupo de logs con retención de 30 días para observabilidad centralizada.

**Pasos de despliegue**:
```bash
cd infra/terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

### 2.2 Alternativa de Despliegue en Microsoft Azure

Para organizaciones que operan sobre Azure, la arquitectura se mapea de forma equivalente:

| Componente AWS | Equivalente en Azure | Rol Arquitectónico |
| :--- | :--- | :--- |
| **Amazon ECS Fargate** | Azure Container Apps / App Service | Cómputo contenerizado sin gestión de VMs |
| **Amazon S3** | Azure Blob Storage (Hot Tier) | Almacenamiento documental cifrado |
| **Amazon DynamoDB** | Azure Cosmos DB (Core SQL API) | Base de datos NoSQL para auditoría |
| **Amazon Bedrock** | Azure OpenAI Service (GPT-4o) | Modelo fundacional y embeddings |
| **CloudWatch Logs** | Azure Monitor / Log Analytics | Agregación de logs estructurados |
| **AWS IAM Roles** | Azure Managed Identities | Autenticación entre servicios sin contraseñas |

---

## 3. Consideraciones para Producción y Seguridad

1. **Gestión de Secretos**: Integración con AWS Secrets Manager o Azure Key Vault para inyección dinámica de credenciales en tiempo de arranque.
2. **Rate Limiting y WAF**: Despliegue de AWS WAF frente al Application Load Balancer con reglas administradas de mitigación de ataques web e IP throttling.
3. **Cache Semántico**: Implementación de Redis (Amazon ElastiCache) para almacenar en caché respuestas de preguntas frecuentes, reduciendo la latencia de 2s a <50ms.
4. **Monitoreo y Alarmas**: Métricas de CloudWatch con alarmas ante picos de errores 5xx, latencias P95 superiores a 5 segundos o intentos repetidos de prompt injection.
