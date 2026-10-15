<!--
# Sync Impact Report
- Version change: Uninitialized template -> 1.0.0
- Ratification Date: 2026-10-15
- List of modified principles:
  - PRINCIPLE_1 -> I. Cumplimiento estricto del alcance
  - PRINCIPLE_2 -> II. Arquitectura simple y mantenible
  - PRINCIPLE_3 -> III. RAG fundamentado y verificable
  - PRINCIPLE_4 -> IV. Agente con herramientas controladas
  - PRINCIPLE_5 -> V. Seguridad por diseño
  - Added: VI. Infraestructura reproducible mediante Terraform
  - Added: VII. Calidad y pruebas basadas en evidencia
  - Added: VIII. Observabilidad y trazabilidad
  - Added: IX. Uso responsable del desarrollo asistido por IA
  - Added: X. Documentación y transparencia
- Added sections:
  - Propósito
  - Flujo obligatorio de trabajo
  - Governance: Criterio de resolución de conflictos, Condición de cumplimiento, Procedimiento de enmienda y versionado
- Removed sections:
  - None (plantilla base inicial reemplazada con valores concretos)
- Follow-up TODOs:
  - None
-->

# Enterprise AI Operations Assistant Constitution

## Propósito

Establecer los principios, restricciones y criterios de calidad que deben respetarse durante el diseño, desarrollo, prueba y despliegue del Enterprise AI Operations Assistant.

Esta constitución es la referencia de máxima autoridad técnica para las decisiones de arquitectura, desarrollo y uso de herramientas de desarrollo asistido por inteligencia artificial.

## Core Principles

### I. Cumplimiento estricto del alcance
La solución DEBE satisfacer los requisitos explícitos de la prueba técnica antes de incorporar mejoras opcionales.

- NO implementar funcionalidades ajenas al caso de negocio.
- NO añadir un frontend independiente.
- NO incorporar integraciones corporativas reales fuera del alcance definido.
- NO introducir CI/CD, microservicios adicionales ni componentes innecesarios.
- Toda funcionalidad adicional DEBE justificarse por un requisito de aceptación concreto.

*Razón*: Evitar sobreingeniería, dispersión de esfuerzo y asegurar la entrega precisa de los entregables evaluables.

### II. Arquitectura simple y mantenible
La implementación DEBE favorecer una arquitectura modular, con responsabilidades claras y dependencias explícitas.

- Utilizar Python y FastAPI para el backend.
- Separar de forma estricta: API, procesamiento RAG, lógica del agente, herramientas y persistencia.
- Evitar abstracciones innecesarias o capas intermedias que no aporten valor verificable.
- Preferir dependencias activamente mantenidas y compatibles.
- NO introducir frameworks de agentes adicionales si no aportan valor verificable demostrable.
- Documentar de manera explícita las decisiones arquitectónicas relevantes (ADRs / docstrings / notas de diseño).

*Razón*: Mantener el código legible, depurable y auditable sin introducir sobrecostes cognitivos.

### III. RAG fundamentado y verificable
El asistente DEBE generar respuestas sustentadas exclusivamente en la documentación disponible y verificable.

- Implementar de forma robusta las etapas de ingesta, chunking, embeddings, almacenamiento y recuperación.
- Conservar y propagar metadatos que permitan identificar con precisión las fuentes documentales.
- Devolver siempre referencias verificables asociadas a los fragmentos recuperados.
- Abstenerse terminantemente de inventar información cuando la evidencia sea insuficiente o inexistente.
- Diferenciar con total claridad los datos recuperados de las inferencias generadas por el modelo.
- Evaluar formalmente la calidad de la recuperación y la fundamentación de las respuestas.

*Razón*: Prevenir alucinaciones y garantizar que las operaciones corporativas se basen en datos fidedignos.

### IV. Agente con herramientas controladas
El agente DEBE utilizar herramientas explícitas para realizar las acciones requeridas.

- Implementar al menos dos herramientas funcionales con propósito bien definido.
- Definir esquemas rigurosos de entrada y salida (vía Pydantic o equivalente).
- Validar exhaustivamente los argumentos antes de ejecutar cualquier operación.
- Limitar las herramientas de forma estricta a las operaciones autorizadas.
- NO conceder al modelo acceso arbitrario a la infraestructura, base de datos o sistema operativo.
- Registrar detalladamente las ejecuciones de herramientas y sus resultados relevantes.
- NO afirmar que una acción se ejecutó si no existe evidencia directa y verificable de su resultado.

*Razón*: Prevenir ejecuciones accidentales, mitigar vectores de escalada y asegurar la idempotencia y seguridad operativa.

### V. Seguridad por diseño
La seguridad DEBE formar parte integral de la implementación y no limitarse a recomendaciones documentales.

- Aplicar el principio de mínimos privilegios en IAM y accesos.
- Mantener credenciales y secretos estrictamente fuera del código fuente.
- NO subir archivos `.env`, credenciales ni estados sensibles de Terraform al repositorio de control de versiones.
- Validar entradas, tipos, tamaños y formatos de archivos en cada punto de ingesta o API.
- Tratar todo contenido documental como información potencialmente no confiable (defensa en profundidad).
- Mitigar activamente intentos de prompt injection y manipulación contextual.
- Evitar la exposición de datos sensibles en respuestas y logs.
- Manejar errores de forma segura sin revelar trazas internas ni información confidencial.

*Razón*: Proteger la integridad de la infraestructura y cumplir con estándares de seguridad empresariales.

### VI. Infraestructura reproducible mediante Terraform
Todos los recursos de infraestructura DEBEN declararse como código reproducible.

- Utilizar Terraform y el proveedor oficial de AWS.
- Separar las configuraciones en archivos modulares con responsabilidades claras (p. ej., `main.tf`, `variables.tf`, `outputs.tf`).
- Parametrizar la región y los valores específicos del entorno.
- Aplicar el principio de mínimo privilegio a todos los recursos creados.
- Ejecutar `terraform fmt`, `terraform validate` y revisar `terraform plan` antes de cualquier despliegue.
- NO almacenar el estado de Terraform en el repositorio.
- Documentar los prerrequisitos, el despliegue y el procedimiento de limpieza y destrucción de recursos.
- Verificar la compatibilidad y disponibilidad de los recursos antes de definirlos.
- NO declarar un despliegue exitoso sin haberlo ejecutado y comprobado empíricamente.

*Razón*: Garantizar reproducibilidad exacta, evitar desvíos manuales y permitir un aprovisionamiento limpio y seguro.

### VII. Calidad y pruebas basadas en evidencia
La calidad DEBE demostrarse mediante pruebas ejecutables y resultados verificables.

- Utilizar `pytest` para la suite de pruebas automatizadas.
- Cubrir los flujos principales y los escenarios de error esperados.
- Incluir al menos cinco casos específicos de evaluación de respuestas.
- Probar explícitamente: ausencia de información, mitigación de prompt injection y uso correcto de herramientas.
- Registrar resultados observados y desviaciones técnicas.
- NO inventar métricas ni presentar pruebas no ejecutadas como exitosas.
- Mantener los datos de prueba sintéticos o apropiadamente autorizados.

*Razón*: Respaldar cada afirmación de funcionamiento con artefactos de prueba reproducibles.

### VIII. Observabilidad y trazabilidad
El sistema DEBE permitir comprender con precisión qué ocurrió durante cada interacción.

- Registrar eventos relevantes con estructura consistente (logging estructurado).
- Incluir identificadores de interacción (correlation/interaction IDs) cuando corresponda.
- Registrar errores y duración de las operaciones clave.
- Mantener trazabilidad de fuentes documentales y herramientas utilizadas en cada consulta.
- NO registrar secretos, credenciales ni información sensible en los logs.
- Diferenciar claramente entre errores de aplicación, errores de servicios externos y resultados funcionales negativos.

*Razón*: Facilitar el diagnóstico rápido de incidentes y garantizar la auditabilidad de las operaciones.

### IX. Uso responsable del desarrollo asistido por IA
Las herramientas de desarrollo asistido podrán utilizarse para acelerar la implementación, pero todo código generado DEBE ser revisado y validado.

- Documentar explícitamente qué tareas se apoyaron con IA.
- Revisar a fondo la corrección, seguridad y mantenibilidad del código generado.
- Ejecutar pruebas automáticas sobre todos los cambios relevantes.
- NO aceptar automáticamente recomendaciones de arquitectura o seguridad sin análisis crítico previo.
- NO compartir credenciales, datos confidenciales ni documentos internos en herramientas no autorizadas.
- Registrar los riesgos identificados y sus correspondientes medidas de mitigación.
- El desarrollador conserva siempre la responsabilidad final sobre el código entregado.

*Razón*: Asegurar que la asistencia de IA incremente la productividad sin degradar el rigor técnico ni la seguridad.

### X. Documentación y transparencia
La documentación DEBE corresponder de forma fidedigna con el comportamiento real del sistema.

- Mantener el `README.md` permanentemente actualizado.
- Documentar arquitectura, configuración, endpoints y guías de despliegue.
- Explicar las decisiones técnicas relevantes y los trade-offs considerados.
- Identificar con honestidad las limitaciones y funcionalidades pendientes.
- Incluir evidencias de pruebas reales ejecutadas.
- Distinguir claramente entre implementación completada, configuración pendiente y mejoras futuras.

*Razón*: Garantizar claridad para evaluadores, mantenedores y usuarios, eliminando cualquier ambigüedad sobre el estado del proyecto.

## Flujo obligatorio de trabajo

Todo desarrollo dentro del proyecto DEBE seguir el siguiente flujo secuencial:

1. **Revisar los requisitos**: Analizar en detalle los requerimientos de la especificación técnica.
2. **Definir criterios de aceptación**: Establecer las condiciones verificables que definirán el éxito.
3. **Diseñar la solución mínima**: Priorizar la alternativa arquitectónica más simple y mantenible.
4. **Implementar una funcionalidad por vez**: Progresión atómica y modular de los cambios.
5. **Ejecutar pruebas correspondientes**: Validar mediante `pytest` y pruebas de evaluación.
6. **Revisar seguridad y observabilidad**: Verificar mitigaciones, ausencia de fugas y trazabilidad de logs.
7. **Validar infraestructura**: Aplicar validaciones de Terraform (`fmt`, `validate`, `plan`).
8. **Actualizar documentación**: Reflejar el estado real, limitaciones identificadas y pasos de ejecución.

## Governance

### Criterio de resolución de conflictos
En caso de discrepancia o conflicto entre una implementación propuesta y las directrices del proyecto, prevalecerán, en este orden estricto de precedencia:

1. Los requisitos y restricciones explícitos de la prueba técnica.
2. Los principios de seguridad y protección de datos.
3. Los criterios de aceptación de la especificación activa.
4. Los principios fundamentales de esta constitución.
5. Las preferencias individuales de implementación.

Cualquier desviación respecto a esta constitución DEBE quedar explícitamente documentada y justificada.

### Condición de cumplimiento
Una implementación NO se considerará conforme por el simple hecho de compilar o desplegar. Deberá cumplir la totalidad de los requisitos aplicables, contar con pruebas automatizadas y documentación verificables, y declarar de forma honesta sus limitaciones.

### Procedimiento de enmienda y versionado
- **Versionado Semántico (`CONSTITUTION_VERSION`)**:
  - **MAJOR**: Modificaciones, eliminaciones o redefiniciones incompatibles en los principios o gobernanza.
  - **MINOR**: Adición de nuevos principios o secciones, o ampliación material de las directrices existentes.
  - **PATCH**: Correcciones de redacción, erratas, aclaraciones o ajustes no semánticos.
- **Enmiendas**: Toda modificación a esta constitución requiere actualización del informe de impacto (Sync Impact Report), revisión de coherencia con las especificaciones activas y ratificación formal.

**Version**: 1.0.0 | **Ratified**: 2026-10-15 | **Last Amended**: 2026-10-15
