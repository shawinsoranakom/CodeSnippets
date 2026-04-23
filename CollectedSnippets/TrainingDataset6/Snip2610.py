def test_orjson_response_emits_deprecation_warning():
    with pytest.warns(FastAPIDeprecationWarning, match="ORJSONResponse is deprecated"):
        ORJSONResponse(content={"hello": "world"})