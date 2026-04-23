def test_internal_error(mod: ModuleType):
    client = TestClient(mod.app)
    with pytest.raises(mod.InternalError) as exc_info:
        client.get("/items/portal-gun")
    assert (
        exc_info.value.args[0] == "The portal gun is too dangerous to be owned by Rick"
    )