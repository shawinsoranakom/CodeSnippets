def test_encode_pure_path():
    test_path = PurePath("/foo", "bar")

    assert jsonable_encoder({"path": test_path}) == {"path": str(test_path)}