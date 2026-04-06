def get_client(mod):
    client = TestClient(mod.app)
    return client