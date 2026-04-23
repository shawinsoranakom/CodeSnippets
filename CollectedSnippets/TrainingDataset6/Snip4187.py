def client_fixture(app: FastAPI):
    return TestClient(app)