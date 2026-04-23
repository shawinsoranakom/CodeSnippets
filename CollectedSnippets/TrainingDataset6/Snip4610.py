def get_client(request: pytest.FixtureRequest):
    mod = importlib.import_module(f"docs_src.custom_request_and_route.{request.param}")

    @mod.app.get("/check-class")
    async def check_gzip_request(request: Request):
        return {"request_class": type(request).__name__}

    client = TestClient(mod.app)
    return client