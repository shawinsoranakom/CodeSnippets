def get_client(mod: ModuleType):
    client = TestClient(mod.app)
    client.headers.clear()
    return client