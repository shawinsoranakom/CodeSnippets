def client_fixture():
    with TestClient(app) as c:
        yield c