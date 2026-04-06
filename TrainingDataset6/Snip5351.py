def get_client(mod: ModuleType):
    client = TestClient(mod.app)

    return client