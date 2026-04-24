import asyncio
from surrealdb import AsyncSurreal
from models import Article

async def main():
    print("Conectando a SurrealDB...")
    # Usando el context manager asíncrono
    async with AsyncSurreal("ws://localhost:8000/rpc") as db:
        await db.signin({"user": "root", "pass": "root"})
        await db.use("mi_namespace", "mi_datos")
        
        # Crear un artículo usando nuestro modelo de Pydantic
        new_article = Article(title="SurrealDB Python v2", published=True, tags=["python", "async", "pydantic"])
        
        print("Insertando artículo en SurrealDB...")
        # Guardar en la base de datos (convertido a dict)
        created_records = await db.create("article", new_article.model_dump(exclude_none=True))
        print("Registro creado con ID:", created_records[0]["id"] if created_records else "N/A")
        
        print("\nConsultando todos los artículos...")
        articles_data = await db.select("article")
        
        print("\nDatos devueltos desde SurrealDB, validados por Pydantic:")
        for record in articles_data:
            # Pasamos los datos leídos de SurrealDB a Pydantic
            article = Article(**record)
            print(article.model_dump_json(indent=2))

if __name__ == "__main__":
    asyncio.run(main())
