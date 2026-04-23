def get_client() -> TestClient:
    from docs_src.conditional_openapi import tutorial001_py310

    importlib.reload(tutorial001_py310)

    client = TestClient(tutorial001_py310.app)
    return client