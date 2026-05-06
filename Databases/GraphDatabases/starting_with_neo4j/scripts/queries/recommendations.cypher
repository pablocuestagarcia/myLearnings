MATCH (u:User {name: 'Ana'})-[:FRIENDS_WITH*1..2]-(friend:User)-[:LIKES]->(recMovie:Movie)
WHERE NOT (u)-[:LIKES]->(recMovie)
RETURN recMovie.title AS PeliculaRecomendada, count(friend) AS NumeroDeAmigosQueRecomiendan
ORDER BY NumeroDeAmigosQueRecomiendan DESC
