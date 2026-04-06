def test_fastapi_error(mod: ModuleType):
    client = TestClient(mod.app)
    with pytest.raises(FastAPIError) as exc_info:
        client.get("/items/portal-gun")
    assert "raising an exception and a dependency with yield" in exc_info.value.args[0]