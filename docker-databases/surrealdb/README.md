# SurrealDB Playground

SurrealDB es una base de datos innovadora, que se promociona como la base de datos "definitiva" serverless, combinando documentos, relacional, temporal y grafos.

## Iniciar el entorno

```bash
docker compose up -d
```

## Credenciales de Conexión y Setup

- **Host (HTTP/WS):** `localhost`
- **Puerto:** `8000`
- **Usuario:** `root`
- **Contraseña:** `root`

*Nota: SurrealDB no fuerza el uso de una base de datos/namespace específicos hasta que te conectas y los "Usas".*

## Como interactuar

Puedes interactuar con SurrealDB mediante HTTP REST (ej. Postman/Curl) o instalando el SurrealDB CLI en tu máquina local.

También disponen del [Surrealist](https://surrealist.app/), una aplicación web y de escritorio que sirve como interfaz visual increíble (similar al browser de Neo4j o DBeaver). Puedes usar el UI web y poner `http://localhost:8000` con `root` y `root` para conectarte.

### Ejemplo en SurrealQL

El lenguaje es SurrealQL, parecido a SQL.

```surrealql
-- Usar namespace y database (los crea si no existen)
USE NS mi_namespace DB mi_datos;

-- Crear un documento ("tabla" de persona)
CREATE person:1 SET 
  name = 'Pablo',
  role = 'Developer',
  created_at = time::now();

-- Insertar con ID autogenerado
CREATE person SET name = 'John Doe';

-- Modificar data
UPDATE person:1 SET role = 'Senior Developer';

-- Ver la data
SELECT * FROM person;
```

También puedes crear relaciones como si fuera un grafo (ej. `RELATE person:1->wrote->article:1`).

## Caso de Uso Práctico: Multi-Modelo (Documentos + Grafos) (Complejidad Media-Baja)

SurrealDB permite mezclar la flexibilidad de documentos JSON con las consultas relacionales de los grafos.

```surrealql
-- 1. Asegurar el namespace y base de datos
USE NS mi_namespace DB mi_datos;

-- 2. Crear Usuarios (Documentos) con campos anidados
CREATE user:pedro CONTENT {
    name: 'Pedro Martinez',
    contact: { email: 'pedro@example.com', phone: '123456789' },
    skills: ['Rust', 'SurrealDB', 'TypeScript']
};

CREATE user:lucia CONTENT {
    name: 'Lucia Gomez',
    contact: { email: 'lucia@example.com' },
    skills: ['Python', 'Data Science']
};

-- 3. Crear un Artículo (Documento)
CREATE article:surreal_intro CONTENT {
    title: 'Introducción a SurrealDB',
    published: true,
    tags: ['database', 'graph']
};

-- 4. Crear Relaciones Directas (Grafo)
-- Pedro escribió el artículo
RELATE user:pedro->wrote->article:surreal_intro SET time.created = time::now();
-- Lucía leyó el artículo y le dio rating
RELATE user:lucia->read->article:surreal_intro SET rating = 5;

-- 5. PRUEBA 1: Consultas por arrays anidados en documentos
SELECT name, contact.email FROM user WHERE 'SurrealDB' IN skills;

-- 6. PRUEBA 2: Consulta de grafo inverso (¿Quién leyó lo que escribió Pedro?)
SELECT ->wrote->article<-read<-user.name AS lectores FROM user:pedro;
```
