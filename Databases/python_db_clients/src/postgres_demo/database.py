from sqlmodel import SQLModel, create_engine, Session

# Credenciales basadas en el docker-compose de postgres
DATABASE_URL = "postgresql+psycopg://user:password@localhost:5432/advanced_db"

engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    # Crea las tablas definidas en los modelos (si no existen)
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
