def test_invalid_response_model(module_name: str) -> None:
    with pytest.raises(FastAPIError):
        importlib.import_module(f"docs_src.response_model.{module_name}")