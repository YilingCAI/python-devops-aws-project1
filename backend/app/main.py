from fastapi import FastAPI
from  models import Base 
from database import engine
from routers import auth, todos, users
from starlette.staticfiles import StaticFiles

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory='static'), name='static')


@app.get("/healthy")
async def health_check():
    return {'status': 'healthy'}

app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(users.router)