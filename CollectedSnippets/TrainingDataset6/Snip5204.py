def test_verify_password(mod: ModuleType):
    assert mod.verify_password(
        "secret", mod.fake_users_db["johndoe"]["hashed_password"]
    )