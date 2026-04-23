def test_pep695_type_dependencies():
    app = FastAPI()

    @app.get("/")
    async def get_with_dep(value: DependedValue) -> str:  # noqa
        return f"value: {value}"

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.text == '"value: 123"'