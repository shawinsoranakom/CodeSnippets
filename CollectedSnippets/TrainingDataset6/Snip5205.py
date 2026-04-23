def test_get_password_hash(mod: ModuleType):
    assert mod.get_password_hash("johndoe")