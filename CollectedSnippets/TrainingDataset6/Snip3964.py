def get_client():
    from enum import Enum

    app = FastAPI()

    class PlatformRole(str, Enum):
        admin = "admin"
        user = "user"

    class OtherRole(str, Enum): ...

    class User(BaseModel):
        username: str
        role: PlatformRole | OtherRole

    @app.get("/users")
    async def get_user() -> User:
        return {"username": "alice", "role": "admin"}

    client = TestClient(app)
    return client