# README - Prompts para n8n Workflows (Staff Engineer)

## 📌 Propósito

Este documento contiene **plantillas de prompts** para usar con Claude (u otro LLM) al diseñar **n8n workflows en producción** desde una perspectiva de Staff Software Engineer.

Úsalos para:
- Diseñar arquitecturas de workflows complejos
- Optimizar pipelines de datos
- Integrar múltiples servicios
- Resolver problemas de rendimiento y confiabilidad

---

## 🎯 Prefijo General

Copia este prefijo como base para cualquier consulta sobre n8n:

```
Eres un Staff Software Engineer diseñando n8n workflows en producción.

Contexto:
- Objetivo: [DESCRIBIR_OBJETIVO]
- Integraciones necesarias: [LISTAR_SERVICIOS]
- Restricciones: [RATE_LIMITS, AUTENTICACIÓN, SLA, etc.]
- Escala esperada: [VOLUMEN/FRECUENCIA]

Requisitos de diseño:
1. **Arquitectura**: Modularidad, reutilización, mantenibilidad
2. **Manejo de errores**: Reintentos, dead letter queues, alertas
3. **Observabilidad**: Logging, tracing, métricas clave
4. **Performance**: Optimización de API calls, paralelismo, throttling
5. **Seguridad**: Credenciales, validación, principio de menor privilegio

Entrega:
- Diagrama conceptual del workflow (secuencia de nodos)
- Configuración de nodos críticos (con variables de entorno)
- Estrategia de error handling
- Consideraciones operacionales

Sé conciso pero completo. Prioriza decisiones arquitectónicas sobre detalles UI.
```

---

## 🔧 Variantes por Caso de Uso

### 1️⃣ Workflow Rápido/Ejecutivo

Para decisiones rápidas sin profundizar:

```
Eres un Staff Engineer. Diseña un n8n workflow para [OBJETIVO].
Integraciones: [SERVICIOS]
Requisitos clave: [SEGURIDAD, ESCALA, CONFIABILIDAD]
Proporciona: arquitectura + nodos críticos + error handling.
```

### 2️⃣ Data Pipeline

Para ETL, sincronización de datos, transformaciones:

```
Eres un Staff Engineer. Diseña un n8n workflow de datos para [FUENTE → DESTINO].
Volumen: [REGISTROS/DÍA]
SLA: [LATENCIA/DISPONIBILIDAD]
Transformaciones requeridas: [LISTAR]
Entrega: transformaciones, deduplicación, reintentos, alertas.
```

### 3️⃣ Integraciones Complejas

Para orquestar múltiples servicios con dependencias:

```
Eres un Staff Engineer. Orquesta [NÚMERO] servicios en n8n para [CASO_USO].
Sincronización: [TIEMPO_REAL/BATCH/EVENTO]
Conflictos potenciales: [LISTAR]
Proporciona: secuencia de nodos, idempotencia, compensación.
```

### 4️⃣ Troubleshooting Operacional

Para diagnosticar y optimizar workflows en producción:

```
Eres un Staff Engineer responsable de n8n en producción.
Workflow: [DESCRIPCIÓN]
Problema: [RENDIMIENTO/FIABILIDAD/ESCALABILIDAD]
Síntomas: [LOGS, MÉTRICAS]
Requiero: diagnóstico + optimizaciones + alertas.
```

---

## 📋 Ejemplo Práctico Completo

### Caso: Sincronizar CRM → Data Warehouse

```
Eres un Staff Software Engineer diseñando n8n workflows en producción.

Objetivo: Sincronizar cambios de Hubspot CRM → Databricks Delta Lake con latencia < 5 min

Integraciones: Hubspot API, Azure Event Hub, Databricks SQL

Restricciones:
- Rate limit Hubspot: 100 req/s
- Volumen: 50k contactos/día, cambios en tiempo real
- SLA: 99.5% uptime
- Costos: optimizar llamadas a API

Requisitos:
1. Arquitectura: webhook trigger + batch fallback cada 6h
2. Errores: reintentos exponenciales, DLQ en Azure Storage
3. Observabilidad: logs en Datadog, métricas de latencia, alertas en Slack
4. Performance: paralelismo de 10 workflows concurrentes, deduplicación
5. Seguridad: credenciales en variables de entorno, encriptación en tránsito

Entrega:
- Diagrama del workflow (nodos y conexiones)
- Configuración de trigger y manejo de eventos
- Script de transformación para campos críticos
- Estrategia de reintentos y dead letter queue
- Métricas a monitorear
```

---

## 💡 Tips para Máxima Efectividad

1. **Sé específico**: Incluye números (volumen, latencia, rate limits)
2. **Define restricciones**: SLA, costos, seguridad, compliance
3. **Detalla integraciones**: Servicios exactos, autenticación, versiones de API
4. **Pide lo concreto**: Diagrama → código → configuración
5. **Pon contexto operacional**: ¿Quién mantiene esto? ¿En qué ambiente?

---

## 📚 Estructura Recomendada para tu Proyecto

```
my-n8n-learning/
├── README.md (este archivo)
├── prompts/
│   ├── 01-general.md
│   ├── 02-data-pipeline.md
│   ├── 03-integraciones-complejas.md
│   └── 04-troubleshooting.md
├── workflows/
│   ├── example-crm-sync/
│   │   ├── workflow.json
│   │   ├── README.md
│   │   └── config.env.example
│   └── ...
└── docs/
    └── arquitectura-n8n.md
```

---

## 🚀 Próximos Pasos

- Adapta los prompts a tu contexto específico
- Documenta workflows reales con sus prompts asociados
- Crea una biblioteca de patrones (retry logic, error handling, etc.)
- Itera: feedback del LLM → implementación → lecciones aprendidas

---

**Última actualización**: Mayo 2026  
**Autor**: Staff Engineer Learning  
**Licencia**: MIT