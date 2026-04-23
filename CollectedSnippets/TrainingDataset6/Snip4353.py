def test_stringified_annotation():
    # python3.14: Use forward reference without "from __future__ import annotations"
    async def get_current_user() -> DummyUser | None:
        return None

    app = FastAPI()

    client = TestClient(app)

    @app.get("/")
    async def get(
        current_user: Annotated[DummyUser | None, Depends(get_current_user)],
    ) -> str:
        return "hello world"

    response = client.get("/")
    assert response.status_code == 200