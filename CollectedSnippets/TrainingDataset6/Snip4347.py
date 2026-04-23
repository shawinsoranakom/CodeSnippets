def client_fixture() -> TestClient:
    app = FastAPI()

    @app.get("/")
    async def get_people(client: Client) -> list:
        return await client.get_people()

    client = TestClient(app)
    return client