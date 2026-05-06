from sqlmodel import Session, select
from database import create_db_and_tables, engine
from models import User

def create_users():
    user_1 = User(name="Alice", email="alice@example.com", age=30)
    user_2 = User(name="Bob", email="bob@example.com", age=25)

    with Session(engine) as session:
        session.add(user_1)
        session.add(user_2)
        session.commit()
        
        # Refrescar para obtener el ID autogenerado
        session.refresh(user_1)
        session.refresh(user_2)
        
        print("Usuarios creados:")
        print(user_1)
        print(user_2)

def select_users():
    with Session(engine) as session:
        statement = select(User).where(User.age > 20)
        results = session.exec(statement)
        users = results.all()
        
        print("\nUsuarios en la base de datos (edad > 20):")
        for user in users:
            print(user)

def main():
    print("Inicializando la base de datos PostgreSQL...")
    create_db_and_tables()
    
    print("\nInsertando datos...")
    create_users()
    
    print("\nConsultando datos...")
    select_users()

if __name__ == "__main__":
    main()
