from database import driver, close_driver
from models import Person, PersonWithFriends

def create_friendship(tx, person1_name, person1_age, person2_name, person2_age):
    query = (
        "MERGE (p1:Person {name: $person1_name}) "
        "ON CREATE SET p1.age = $person1_age "
        "MERGE (p2:Person {name: $person2_name}) "
        "ON CREATE SET p2.age = $person2_age "
        "MERGE (p1)-[:FRIENDS_WITH]->(p2)"
    )
    tx.run(query, person1_name=person1_name, person1_age=person1_age, 
                  person2_name=person2_name, person2_age=person2_age)

def get_person_and_friends(tx, name):
    query = (
        "MATCH (p:Person {name: $name}) "
        "OPTIONAL MATCH (p)-[:FRIENDS_WITH]->(f:Person) "
        "RETURN p.name AS name, p.age AS age, collect(f.name) AS friends"
    )
    result = tx.run(query, name=name)
    record = result.single()
    if record:
        return PersonWithFriends(name=record["name"], age=record["age"], friends=record["friends"])
    return None

def main():
    print("Conectando a Neo4j...")
    
    with driver.session() as session:
        print("Creando relación de amistad entre Charlie y Diana...")
        session.execute_write(create_friendship, "Charlie", 28, "Diana", 26)
        
        print("Consultando a Charlie y sus amigos...")
        charlie_data = session.execute_read(get_person_and_friends, "Charlie")
        
        if charlie_data:
            print("Datos obtenidos desde Neo4j (Pydantic Model):")
            print(charlie_data.model_dump_json(indent=2))

    close_driver()

if __name__ == "__main__":
    main()
