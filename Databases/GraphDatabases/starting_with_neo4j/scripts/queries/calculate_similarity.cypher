// ==========================================
// CONSULTA 1: Conceptos Compartidos Dierectos
// ==========================================
// ¿Qué conceptos (Nodos) comparte el 'Backend_Auth_API' con el resto de repositorios?
MATCH (r1:Repository {name: 'Backend_Auth_API'})-[]->(sharedConcept)<-[]-(r2:Repository)
RETURN r1.name AS RepoOriginal, 
       r2.name AS RepoComparado, 
       collect(sharedConcept.name) AS ConceptosCompartidos, 
       count(sharedConcept) AS TotalCompartidos
ORDER BY TotalCompartidos DESC;


// ==========================================
// CONSULTA 2: Similitud de Jaccard (Cercanía Semántica)
// ==========================================
// El cálculo evalúa el solapamiento de conceptos: Intersection / Union
MATCH (r1:Repository)-[]->(c1)
WITH r1, collect(id(c1)) AS r1_concepts
MATCH (r2:Repository)-[]->(c2) WHERE r1 <> r2
WITH r1, r1_concepts, r2, collect(id(c2)) AS r2_concepts

// Calcular Intersección
WITH r1, r2, r1_concepts, r2_concepts,
     [x IN r1_concepts WHERE x IN r2_concepts] AS itersection

// Calcular la Similitud usando el algoritmo de Jaccard Math
// Jaccard = (Intersección) / (Conjunto 1 + Conjunto 2 - Intersección)
WITH r1, r2, 
     size(itersection) AS size_intersect,
     size(r1_concepts) AS size_r1,
     size(r2_concepts) AS size_r2
     
WITH r1, r2, 
     size_intersect, 
     (size_r1 + size_r2 - size_intersect) AS size_union

RETURN r1.name AS Repositorio1, 
       r2.name AS Repositorio2, 
       (1.0 * size_intersect / size_union) AS IndiceDeCercania
ORDER BY Repositorio1, IndiceDeCercania DESC;
