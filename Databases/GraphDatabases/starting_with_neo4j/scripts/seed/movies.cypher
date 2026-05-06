CREATE
  // 1. Creamos Nodos de Usuarios
  (ana:User {name: 'Ana'}),
  (bernardo:User {name: 'Bernardo'}),
  (carmen:User {name: 'Carmen'}),
  (david:User {name: 'David'}),
  (elena:User {name: 'Elena'}),

  // 2. Creamos Nodos de Películas
  (m1:Movie {title: 'The Matrix'}),
  (m2:Movie {title: 'Inception'}),
  (m3:Movie {title: 'Interstellar'}),
  (m4:Movie {title: 'El Padrino'}),

  // 3. Creamos relaciones de Amistad (FRIENDS_WITH)
  (ana)-[:FRIENDS_WITH]->(bernardo),
  (ana)-[:FRIENDS_WITH]->(carmen),
  (bernardo)-[:FRIENDS_WITH]->(david),
  (carmen)-[:FRIENDS_WITH]->(elena),
  (david)-[:FRIENDS_WITH]->(elena),

  // 4. Creamos relaciones de Gustos (LIKES)
  (ana)-[:LIKES]->(m1),
  (bernardo)-[:LIKES]->(m1),
  (bernardo)-[:LIKES]->(m2),
  (carmen)-[:LIKES]->(m3),
  (david)-[:LIKES]->(m2),
  (david)-[:LIKES]->(m3),
  (elena)-[:LIKES]->(m4);
