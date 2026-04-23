def test_encode_model_with_pure_posix_path():
    class ModelWithPath(BaseModel):
        path: PurePosixPath

        model_config = {"arbitrary_types_allowed": True}

    obj = ModelWithPath(path=PurePosixPath("/foo", "bar"))
    assert jsonable_encoder(obj) == {"path": "/foo/bar"}