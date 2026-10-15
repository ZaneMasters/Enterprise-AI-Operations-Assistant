# Bitácora de Desarrollo Asistido por IA (AI-CDL)

**Proyecto**: Enterprise AI Operations Assistant  
**Criterio de Gobernanza**: Principio IX de la Constitución (`.specify/memory/constitution.md`)  
**Fecha de Registro**: 2026-10-15  

---

## 1. Declaración de Uso de Herramientas de IA

El desarrollo de este proyecto se apoyó en herramientas de inteligencia artificial para acelerar la estructuración de especificaciones, generación de código modular, diseño de infraestructura en Terraform y suites de prueba automatizadas.

- **Herramientas Utilizadas**: Antigravity IDE (Gemini Flash), Spec Kit (metodología estructurada de especificación a código).
- **Rol del Desarrollador Humano**: Definición de la constitución, revisión arquitectónica, validación de seguridad, corrección de modelos de datos, ejecución de pruebas empíricas y verificación de cero alucinaciones.

---

## 2. Registro de Tareas Apoyadas con IA y Validaciones Humanas

| Fase / Tarea | Asistencia de IA Proporcionada | Validación y Ajuste Humano Realizado | Riesgo Mitigado |
| :--- | :--- | :--- | :--- |
| **Constitución del Proyecto** | Generación de la plantilla base y estructuración en Markdown. | Ratificación manual de los 10 principios, jerarquía de resolución de conflictos y flujo de trabajo obligatorio. | Desviación de requisitos o sobreingeniería. |
| **Especificación Técnica** | Redacción inicial de historias de usuario y casos extremos. | Acotación estricta del alcance (sin frontend independiente, sin integraciones de terceros prematuras). | Inclusión de componentes innecesarios. |
| **Clarificación de Requisitos** | Planteamiento de preguntas interactivas sobre severidad y formatos. | Decisión humana de adoptar 3 niveles deterministas (Alta, Media, Baja) y soporte a Markdown/TXT/PDF. | Reglas de negocio ambiguas o no comprobables. |
| **Diseño RAG y Chunking** | Algoritmo de partición recursiva y cliente ChromaDB. | Calibración empírica del umbral de distancia (0.935) e incorporación de guardrail temático por entidades para forzar abstención estricta. | Falsos positivos de recuperación y alucinaciones. |
| **Herramientas del Agente** | Estructuras de validación con Pydantic v2. | Restricción estricta de alcance: solo lectura de base sintética de solicitudes y cálculo matricial de prioridad. | Ejecución arbitraria de comandos en el SO o acceso no controlado a infraestructura. |
| **Seguridad y Anti-Injection** | Expresiones regulares de detección de inyecciones. | Delimitación estricta de fragmentos mediante etiquetas XML `<context_documents>` e instrucciones de datos pasivos. | Indirect Prompt Injection a través de documentos corporativos. |
| **Infraestructura Terraform** | Plantillas HCL para ECS Fargate, S3 y DynamoDB. | Auditoría de roles IAM aplicando estrictamente el principio de mínimo privilegio y bloqueo de acceso público en S3. | Sobre-otorgación de permisos administrativos (Wildcards IAM). |
| **Suite de Calidad (5 Casos)** | Casos de prueba automatizados con `pytest`. | Verificación empírica de ejecución real: 19 pruebas ejecutadas y 100% aprobadas. | Métricas simuladas o pruebas no ejecutadas. |

---

## 3. Riesgos Identificados y Medidas de Mitigación

1. **Riesgo: Alucinación en Respuestas Operativas**
   - *Mitigación*: Implementación del guardrail de presencia de palabras clave sustantivas en el contexto. Si no hay evidencia textual verificable, el sistema devuelve `ABSTAINED` determinísticamente.
2. **Riesgo: Fuga de Credenciales o Información Sensible**
   - *Mitigación*: Validación con `.gitignore` riguroso, exclusión de archivos `.env`, sanitización de logs estructurados y formateador global de excepciones que nunca expone stack traces de Python al cliente.
3. **Riesgo: Falta de Reproducibilidad en Evaluaciones Locales**
   - *Mitigación*: Persistencia local en ChromaDB y SQLite, permitiendo que la suite completa se ejecute sin requerir credenciales activas de AWS.
