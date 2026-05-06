from surrealdb import AsyncSurreal

async def get_db_context():
    # En versiones modernas de la SDK, se usa el context manager
    db = AsyncSurreal("ws://localhost:8000/rpc")
    await db.connect()
    await db.signin({"user": "root", "pass": "root"})
    await db.use("mi_namespace", "mi_datos")
    return db
