def get_client():
    mod = importlib.import_module(MOD_NAME)
    client = TestClient(mod.app)
    return client