# Procedimiento Operativo: Actualización de Bases de Datos en Producción

**Código de Procedimiento**: SOP-DB-004  
**Versión**: 2.3  
**Vigencia**: 2026-2027  
**Clasificación**: Uso Interno de Operaciones TI  

## 1. Objetivo y Alcance
Este procedimiento establece los pasos obligatorios que todo ingeniero de operaciones y DBA debe cumplir rigurosamente antes, durante y después de ejecutar cualquier migración, actualización de esquema o mantenimiento mayor en los motores de base de datos de producción (Amazon RDS y Aurora PostgreSQL).

## 2. Requisitos Previos y Aprobaciones Obligatorias
Para iniciar una ventana de mantenimiento de base de datos se debe contar con:
1. **Ticket de Cambio Aprobado**: Registro formal en el sistema de gestión con aprobación del Líder de Infraestructura y del Oficial de Seguridad de la Información (CISO).
2. **Copia de Respaldo Inmutable (Snapshot)**: Es estrictamente mandatorio ejecutar un snapshot manual antes de iniciar cualquier cambio. El snapshot debe nombrarse siguiendo la convención `pre-upgrade-YYYYMMDD-DBNAME` y verificar que el estado sea `Available`.
3. **Validación en Entorno de Staging**: El script de actualización o migración debe haberse ejecutado exitosamente en el entorno de pruebas en las últimas 48 horas sin errores de integridad.
4. **Ventana de Mantenimiento Autorizada**: Las actualizaciones sólo pueden programarse entre las 01:00 UTC y las 04:00 UTC de los días martes y jueves para minimizar el impacto a usuarios finales.

## 3. Pasos de Ejecución
1. **Notificación**: Enviar aviso de inicio de ventana al canal `#ops-maintenance`.
2. **Pausa de Tráfico**: Configurar el modo mantenimiento en el Application Load Balancer o activar el desvío temporal de conexiones no esenciales.
3. **Ejecución del Snapshot**: Generar el snapshot manual y esperar confirmación del 100% de finalización.
4. **Aplicación de Migración**: Conectarse a través del host bastión seguro utilizando IAM Database Authentication (no se permiten credenciales maestras estáticas) y ejecutar el script versionado.
5. **Pruebas de Humo (Sanity Check)**: Ejecutar consultas de validación de esquemas y conteo de registros clave para asegurar consistencia de datos.
6. **Reanudación del Tráfico**: Restaurar el balanceador de carga y validar métricas de CPU, conexiones activas y latencia en Amazon CloudWatch.

## 4. Plan de Retorno (Rollback)
Si durante la ejecución se detecta una degradación superior al 15% en los tiempos de respuesta o un error de integridad no recuperable dentro de los primeros 30 minutos:
- Suspender de inmediato la migración.
- Proceder a la restauración de la instancia de base de datos a partir del snapshot manual `pre-upgrade-YYYYMMDD-DBNAME`.
- Redirigir el endpoint CNAME del DNS interno hacia la instancia restaurada.
- Notificar la activación del plan de retorno al equipo de incidentes.
