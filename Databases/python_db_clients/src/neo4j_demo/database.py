from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "secret_password")

driver = GraphDatabase.driver(URI, auth=AUTH)

def close_driver():
    driver.close()
