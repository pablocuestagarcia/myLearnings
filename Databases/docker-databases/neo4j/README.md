# Neo4j (Graph Database Playground)

Neo4j es una base de datos nativa de grafos. En lugar de tablas o documentos, almacena Nodos y Relaciones.

## Iniciar el entorno

```bash
docker compose up -d
```

## Como conectarte

Neo4j incluye un navegador (Browser) genial pre-instalado donde puedes ejecutar consultas y ver los grafos visualmente.

1. Abre tu navegador y ve a: [http://localhost:7474](http://localhost:7474)
2. Loguéate con las siguientes credenciales:
   - **User:** `neo4j`
   - **Password:** `secret_password`

## Protocolo Bolt
Si te conectas de un SDK en tu aplicación (Node.js, Python), usarás el puerto del protocolo **Bolt**:
- **Connection URI:** `bolt://localhost:7687`

## Tus primeras consultas en Cypher

Abre el Neo4j Browser y pega las siguientes consultas para empezar a aprender su lenguaje de consulta (Cypher):

```cypher
// Crear un nodo (Persona)
CREATE (p:Person {name: 'Pablo', role: 'Developer'})
RETURN p

// Crear otro nodo
CREATE (p:Person {name: 'Alice', role: 'Data Scientist'})

// Crear una relación entre ellos
MATCH (a:Person {name: 'Pablo'}), (b:Person {name: 'Alice'})
CREATE (a)-[:KNOWS {since: 2023}]->(b)

// Consultar el grafo entero
MATCH (n) RETURN n
```

## Caso de Uso Práctico: Motor de Recomendaciones (Complejidad Media-Baja)

Neo4j brilla cuando necesitas descubrir relaciones profundas. Aquí crearemos una red social y buscaremos "amigos de amigos" (recomendaciones de amistad) y recomendaciones basadas en intereses.

```cypher
// 1. Limpiar la base de datos (opcional para no mezclar)
MATCH (n) DETACH DELETE n;

// 2. Crear usuarios y sus intereses
CREATE 
  (ana:User {name: 'Ana', age: 28}),
  (juan:User {name: 'Juan', age: 30}),
  (luis:User {name: 'Luis', age: 25}),
  (maria:User {name: 'Maria', age: 29}),
  (tech:Interest {name: 'Tecnología'}),
  (music:Interest {name: 'Música'})

// 3. Crear relaciones de amistad
CREATE 
  (ana)-[:FRIENDS_WITH]->(juan),
  (juan)-[:FRIENDS_WITH]->(luis),
  (juan)-[:FRIENDS_WITH]->(maria)

// 4. Crear relaciones de intereses
CREATE
  (ana)-[:LIKES]->(tech),
  (luis)-[:LIKES]->(tech),
  (maria)-[:LIKES]->(music);

// 5. PRUEBA 1: Recomendación de Amistad (Amigos de amigos que Ana no conoce)
MATCH (ana:User {name: 'Ana'})-[:FRIENDS_WITH]->(amigo)-[:FRIENDS_WITH]->(amigo_de_amigo)
WHERE NOT (ana)-[:FRIENDS_WITH]-(amigo_de_amigo) AND ana <> amigo_de_amigo
RETURN amigo_de_amigo.name AS Recomendacion_Amistad;

// 6. PRUEBA 2: Recomendación basada en intereses comunes
MATCH (u:User)-[:LIKES]->(i:Interest)<-[:LIKES]-(otro:User)
WHERE u.name = 'Ana' AND u <> otro
RETURN otro.name AS Usuarios_Con_Mismos_Intereses, i.name AS Interes_Comun;
```
