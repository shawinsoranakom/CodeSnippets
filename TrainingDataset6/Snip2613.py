def test_ujson_response_emits_deprecation_warning():
    with pytest.warns(FastAPIDeprecationWarning, match="UJSONResponse is deprecated"):
        UJSONResponse(content={"hello": "world"})