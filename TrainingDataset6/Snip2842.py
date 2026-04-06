def test_encode_model_with_pure_windows_path():
    class ModelWithPath(BaseModel):
        path: PureWindowsPath

        model_config = {"arbitrary_types_allowed": True}

    obj = ModelWithPath(path=PureWindowsPath("/foo", "bar"))
    assert jsonable_encoder(obj) == {"path": "\\foo\\bar"}