# Arquitectura: Enterprise AI Operations Assistant (Serverless AWS & Local)

## 1. Diagrama de Arquitectura de la Solución (Nube AWS & Local)

El sistema implementa una arquitectura desacoplada, observable y de bajo costo. Puede ejecutarse tanto en **AWS (Serverless con API Gateway + Lambda + Bedrock)** como en **entorno local (FastAPI + ChromaDB + SQLite)** sin alterar contratos ni interfaces.

```mermaid
graph TB
    subgraph Consumidores["Canales de Consumo"]
        Operador["Operador TI / Postman / Swagger"]
        Auditor["Auditor de Cumplimiento TI"]
    end

    subgraph AWS_Cloud["AWS Cloud Infrastructure (Terraform Managed)"]
        APIGW["Amazon HTTP API Gateway<br/><code>https://rvcbgebxx7.execute-api...</code>"]
        
        subgraph Compute["Cómputo Serverless"]
            Lambda["AWS Lambda (Python 3.12)<br/>FastAPI + Mangum Adapter"]
        end
        
        subgraph SecurityOps["Seguridad & Observabilidad"]
            IAM["AWS IAM Role<br/>Principio de Menor Privilegio"]
            CW["Amazon CloudWatch Logs<br/>Trazabilidad y Correlation IDs"]
        end

        subgraph AIServices["Servicios Cognitivos & LLM"]
            Titan["Amazon Titan Embeddings G1<br/>Vectorización Documental (1536d)"]
            Claude["Amazon Bedrock<br/>Anthropic Claude Haiku 4.5"]
        end

        subgraph StorageAWS["Persistencia en Nube"]
            S3["Amazon S3 Bucket<br/>Documentos Originales Cifrados (SSE-AES256)"]
            Dynamo["Amazon DynamoDB<br/>Tabla de Auditoría On-Demand"]
        end
    end

    subgraph Local_Mode["Modo de Ejecución Local (Offline / Evaluadores)"]
        FastAPILocal["FastAPI + Uvicorn Local (Port 8000)"]
        ChromaLocal["ChromaDB Vector Store (./data/vectorstore)"]
        SQLiteLocal["SQLite History DB (./data/history.db)"]
        MockLLM["Mock Deterministic LLM Generator"]
    end

    %% Flujos Cloud
    Operador -->|HTTPS REST Request| APIGW
    Auditor -->|GET /history| APIGW
    APIGW -->|Proxy HTTP Event| Lambda
    Lambda -->|Assume Role| IAM
    Lambda -->|Logs Estructurados| CW
    Lambda -->|Generar Embeddings de Consulta| Titan
    Lambda -->|Generación Fundamentada| Claude
    Lambda -.->|Docs Backup| S3
    Lambda -.->|Trazas Cloud| Dynamo

    %% Flujos Local
    Operador -.->|Desarrollo Local| FastAPILocal
    FastAPILocal --> ChromaLocal
    FastAPILocal --> SQLiteLocal
    FastAPILocal --> MockLLM
```

---

## 2. Diagrama de Secuencia: Flujo de una Consulta RAG (`POST /chat`)

```mermaid
sequenceDiagram
    autonumber
    actor User as Operador / Postman
    participant GW as HTTP API Gateway
    participant Lmb as AWS Lambda (FastAPI)
    participant Sec as Security Guardrails
    participant RAG as RAG Retriever
    participant Titan as Bedrock Titan Embeddings
    participant Claude as Bedrock Claude Haiku
    participant Hist as History DB (Audit)

    User->>GW: POST /chat {"query": "¿Cuáles son los requisitos previos para actualizar la BD?"}
    GW->>Lmb: Invocación Serverless
    Lmb->>Sec: 1. Validación de Entrada y Detección de Prompt Injection
    alt Prompt Injection Detectado
        Sec-->>User: 200 OK con Estado ERROR y Mensaje de Política de Seguridad
    else Consulta Válida
        Sec->>RAG: 2. Enrutamiento: ¿Requiere Herramienta o Documentación?
        alt Consulta Documental RAG
            RAG->>Titan: 3. Vectorizar Consulta del Usuario (Embedding 1536d)
            Titan-->>RAG: Vector de Consulta
            RAG->>RAG: 4. Búsqueda por Similitud Coseno & Filtrado por Umbral
            alt Similitud Insuficiente o Sin Evidencia
                RAG-->>User: Abstención Formal Determinista (Estado: ABSTAINED)
            else Evidencia Relevante Recuperada
                RAG->>Claude: 5. Invocación con Contexto Aislado en <context_documents>
                Claude-->>RAG: Respuesta Fundamentada con Citas Explícitas
                RAG->>Hist: 6. Persistir Trazabilidad (interaction_id, duración, estado)
                Hist-->>Lmb: Confirmación de Escritura
                Lmb-->>User: 200 OK QueryResponse {status: "SUCCESS", answer, sources}
            end
        end
    end
```

---

## 3. Diagrama de Secuencia: Ingesta y Vectorización Dinámica (`POST /documents`)

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Operador / Administrador
    participant GW as HTTP API Gateway
    participant Lmb as AWS Lambda (FastAPI)
    participant S3 as Amazon S3 Bucket
    participant Titan as Bedrock Titan Embeddings
    participant Chroma as ChromaDB Local

    Admin->>GW: POST /documents (multipart/form-data: .pdf, .md, .txt)
    GW->>Lmb: Evento HTTP Multipart
    Lmb->>Lmb: 1. Validación de Formato & Extracción de Texto (PyPDF / UTF-8)
    Lmb->>Lmb: 2. Chunking Recursivo (chunk_size=500, overlap=50)

    alt Modo Cloud (AWS Lambda)
        Lmb->>S3: 3. Respaldar Binario Original (s3://rag-docs-.../documents/<filename>)
        loop Por cada Fragmento
            Lmb->>Titan: 4. Generar Vector Embedding (amazon.titan-embed-text-v1)
            Titan-->>Lmb: Vector 1536d
        end
        Lmb->>S3: 5. Persistir en Vector Store Dinámico (s3://.../vectorstore/dynamic_chunks.json)
    else Modo Local (Offline)
        Lmb->>Chroma: 3. Indexar Fragmentos en ChromaDB (./data/vectorstore)
    end

    Lmb-->>Admin: 201 Created DocumentIngestResponse {doc_id, chunks_created, message}
```

---

## 4. Justificación de Decisiones de Arquitectura

1. **AWS Lambda + HTTP API Gateway en lugar de ECS Fargate + ALB:**
   - **Costo:** ECS con Application Load Balancer genera un costo fijo aproximado de **$25 - $40 USD/mes** solo por mantener el balanceador encendido sin tráfico. La arquitectura Lambda + HTTP API Gateway tiene **costo $0.00 USD en reposo** y entra holgadamente en el Free Tier de AWS.
   - **Escalabilidad:** Escala instantáneamente de 0 a miles de peticiones por segundo sin necesidad de configurar auto-scaling groups.
2. **Persistencia Dual (Amazon DynamoDB en Cloud + SQLite en Local):**
   - **En Producción (AWS Lambda):** La persistencia inmutable de auditoría se realiza en **Amazon DynamoDB** (`enterprise-ai-assistant-history-production`), garantizando durabilidad y consultas rápidas por Partition Key (`interaction_id`) y Sort Key (`timestamp`), superando la limitación del sistema de archivos efímero de Lambda.
   - **En Desarrollo Local:** Emplea SQLite (`./data/history.db`) permitiendo ejecutar pruebas unitarias (`pytest`) sin necesidad de configurar credenciales de AWS.
3. **Respaldo Documental en Amazon S3 y Embeddings Dinámicos con Titan:**
   - Los documentos cargados por `POST /documents` se archivan con cifrado SSE-AES256 en Amazon S3 y se vectorizan al vuelo con `amazon.titan-embed-text-v1`, permitiendo que el asistente responda de inmediato sobre cualquier nuevo PDF o manual sin re-despliegues.
4. **Dualidad Local / Nube:**
   - Los evaluadores pueden ejecutar la solución en local con `pytest` sin gastar credenciales de nube gracias a ChromaDB + SQLite + Mock Provider, o invocar la URL pública en vivo de AWS.

