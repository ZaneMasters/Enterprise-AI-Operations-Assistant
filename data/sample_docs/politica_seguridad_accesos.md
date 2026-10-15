# Política Corporativa de Seguridad y Gestión de Accesos

**Código de Política**: POL-SEC-012  
**Versión**: 3.1  
**Aprobado por**: Comité de Ciberseguridad y Cumplimiento  

## 1. Principio de Menor Privilegio (Least Privilege)
Todo acceso a los entornos de nube, infraestructura, bases de datos y repositorios de código debe concederse bajo el principio estricto del menor privilegio posible.
- Los usuarios y servicios únicamente tendrán asignados los permisos indispensables para la ejecución de sus responsabilidades laborales inmediatas.
- Queda terminantemente prohibido el uso de credenciales de usuario raíz (`root`) de AWS para labores operativas cotidianas.
- No se permite la generación ni almacenamiento de claves de acceso estáticas (`Access Keys`) para usuarios humanos; se debe emplear AWS IAM Identity Center (Single Sign-On) con roles asumiendo sesiones temporales federadas.

## 2. Autenticación Multifactor (MFA)
- La autenticación multifactor mediante token físico o aplicación TOTP basada en hardware/software es de carácter obligatorio para todos los colaboradores de la organización sin excepción.
- El inicio de sesión en consolas administrativas o acceso mediante SSH a servidores remotos requiere reautenticación MFA si la sesión supera las 8 horas de inactividad.

## 3. Manejo de Secretos y Cero Credenciales en Código
- Toda contraseña, token de API, cadena de conexión a bases de datos o certificado digital debe almacenarse en servicios de gestión de secretos protegidos (AWS Secrets Manager o HashiCorp Vault).
- Queda terminantemente prohibido incluir secretos en archivos de código fuente, scripts, variables de entorno versionadas en Git o documentación compartida.
- La detección de cualquier secreto comprometido en un repositorio de código provocará la revocación inmediata y rotación forzosa de la credencial en un plazo máximo de 60 minutos.

## 4. Requisitos para Despliegues y Cambios en Producción
- Todo despliegue en entornos productivos debe orquestarse mediante infraestructura como código (Terraform) y validarse contra las directrices de seguridad vigentes.
- Se requiere aprobación de al menos dos ingenieros sénior para aplicar cambios en políticas IAM que involucren permisos de administración de datos o red.
