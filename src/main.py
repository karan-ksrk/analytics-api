from contextlib import asynccontextmanager
from fastapi import FastAPI
from api.events import router as event_router
from api.db.session import init_db
from fastapi.middleware.cors import CORSMiddleware
# old way
# @app.on_event("startup")
# def on_startup():
#     print("init method for db")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # before app startup
    init_db()
    yield
    # clean up

app = FastAPI(lifespan=lifespan)
app.include_router(event_router, prefix="/api/events")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def get_root():
    return {"message": "Hello World"}


@app.get("/healthz")
def read_api_health():
    return {"status": "Ok"}
