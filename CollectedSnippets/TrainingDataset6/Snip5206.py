def test_create_access_token(mod: ModuleType):
    access_token = mod.create_access_token(data={"data": "foo"})
    assert access_token