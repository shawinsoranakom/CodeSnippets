def get_client(mod_name: str):
    mod = importlib.import_module(f"docs_src.body_nested_models.{mod_name}")

    client = TestClient(mod.app)
    return client