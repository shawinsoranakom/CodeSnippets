def get_client(mod_name: str) -> TestClient:
    mod = importlib.import_module(f"docs_src.path_operation_configuration.{mod_name}")
    return TestClient(mod.app)