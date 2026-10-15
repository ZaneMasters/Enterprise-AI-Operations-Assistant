# Protocolo Corporativo de Rotación de Claves Criptográficas y Gestión KMS

**Código de Documento**: POL-KMS-042  
**Versión**: 2.0  
**Clasificación**: Confidencial Interno  
**Área Responsable**: Arquitectura de Ciberseguridad y Operaciones Cloud  

---

## 1. Alcance y Frecuencia de Rotación Obligatoria

Este protocolo aplica a todas las Claves de Cliente Administradas (CMK) alojadas en AWS Key Management Service (KMS) y utilizadas para el cifrado de datos en reposo y en tránsito.

1. **Rotación Automática para Datos Financieros**:
   - Todas las claves KMS que protegen bases de datos con transacciones financieras o registros bancarios deben rotarse obligatoriamente de forma anual automática en AWS, y además someterse a una rotación manual de material de clave cada **90 días calendario**.
2. **Periodo de Gracia para Claves Antiguas**:
   - Tras completar una rotación de clave KMS, las aplicaciones disponen de un período de gracia de **7 días hábiles** para completar el recifrado de datos en búfer antes de que la versión anterior sea deshabilitada para operaciones de cifrado.

---

## 2. Parámetros Criptográficos Estándar

- **Algoritmo de Cifrado Simétrico**: Es obligatorio el uso exclusivo de **AES-GCM con claves de 256 bits** (`AES_256_GCM`). Queda estrictamente vetado el uso de algoritmos DES, 3DES o ECB.
- **Envelope Encryption**: Para archivos y payloads mayores a 4 KB, las aplicaciones deben implementar cifrado por sobre (*Envelope Encryption*) generando Data Keys efímeras a través de la API `kms:GenerateDataKey`. Las claves de datos en texto plano deben ser destruidas de memoria RAM inmediatamente tras el cifrado.

---

## 3. Protocolo de Destrucción de Material Criptográfico

La eliminación definitiva o destrucción programada de una clave criptográfica (con un periodo de espera de 30 días en AWS KMS) únicamente puede ser autorizada si se cumplen los siguientes requisitos:

1. **Aprobación Mancomunada**: Se requiere la firma digital y consentimiento explícito de al menos **dos Oficiales de Seguridad (el CISO y el Security Operations Lead)**.
2. **Auditoría de Dependencias**: El equipo de SRE debe certificar que no existen snapshots en Amazon S3 o tablas en Amazon DynamoDB dependientes del ARN de dicha clave mediante una consulta en AWS CloudTrail durante los últimos 180 días.
