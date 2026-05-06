import os
from neo4j import GraphDatabase

# En Docker usaremos el nombre del servicio como host: neo4j_helloworld
URI = os.getenv("NEO4J_URI", "bolt://neo4j_helloworld:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "helloworld123")

# Definición manual de un "Modelo Semántico" de repositorios y conceptos
REPOSITORIES = [
    {
        "name": "Backend_Auth_API",
        "language": "Python",
        "framework": "Django",
        "topics": ["Backend", "Security", "API"]
    },
    {
        "name": "Frontend_Dashboard",
        "language": "TypeScript",
        "framework": "React",
        "topics": ["Frontend", "UI", "Dashboard"]
    },
    {
        "name": "Data_Pipeline_Service",
        "language": "Python",
        "framework": "Pandas",
        "topics": ["Data Science", "Backend", "Data Processing"]
    },
    {
        "name": "Secure_Graph_Service",
        "language": "Python",
        "framework": "FastAPI",
        "topics": ["Backend", "Security", "Graph Databases"]
    },
    {
        "name": "Go_Microservice_Auth",
        "language": "Go",
        "framework": "Gin",
        "topics": ["Backend", "Security", "Microservices"]
    }
]

def seed_semantic_data(driver):
    with driver.session() as session:
        # 1. Limpiar datos viejos de repositorios y semántica para empezar limpio
        session.run("MATCH (n:Repository) DETACH DELETE n;")
        session.run("MATCH (n:Language) DETACH DELETE n;")
        session.run("MATCH (n:Framework) DETACH DELETE n;")
        session.run("MATCH (n:Topic) DETACH DELETE n;")

        print("Base de datos limpiada, insertando modelo semántico...")

        # 2. Insertar Repo y conectar con sus conceptos semánticos
        insert_query = """
        // Crear Repositorio
        MERGE (r:Repository {name: $name})
        
        // Crear/Relacionar Lenguaje
        MERGE (l:Language {name: $language})
        MERGE (r)-[:USES_LANGUAGE]->(l)

        // Crear/Relacionar Framework
        MERGE (f:Framework {name: $framework})
        MERGE (r)-[:USES_FRAMEWORK]->(f)

        // Crear/Relacionar Topics de forma dinámica
        WITH r, $topics AS topics_list
        UNWIND topics_list AS t
        MERGE (topic:Topic {name: t})
        MERGE (r)-[:HAS_TOPIC]->(topic)
        """
        
        for repo_data in REPOSITORIES:
            session.run(insert_query, **repo_data)
            print(f"Repo '{repo_data['name']}' insertado con su relaciones semánticas.")

if __name__ == "__main__":
    try:
        # Se conecta a la base de datos
        with GraphDatabase.driver(URI, auth=(USER, PASSWORD)) as driver:
            driver.verify_connectivity()
            print("Conectado a Neo4j correctamente!")
            seed_semantic_data(driver)
            print("¡Grafo de conocimiento semántico generado con éxito!")
    except Exception as e:
        print(f"Error al conectar o insertar en Neo4j: {e}")
