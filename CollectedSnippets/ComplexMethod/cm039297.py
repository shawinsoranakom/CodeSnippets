def test_method_metadata_request():
    mmr = MethodMetadataRequest(owner="test", method="fit")

    with pytest.raises(ValueError, match="The alias you're setting for"):
        mmr.add_request(param="foo", alias=1.4)

    mmr.add_request(param="foo", alias=None)
    assert mmr.requests == {"foo": None}
    mmr.add_request(param="foo", alias=False)
    assert mmr.requests == {"foo": False}
    mmr.add_request(param="foo", alias=True)
    assert mmr.requests == {"foo": True}
    mmr.add_request(param="foo", alias="foo")
    assert mmr.requests == {"foo": True}
    mmr.add_request(param="foo", alias="bar")
    assert mmr.requests == {"foo": "bar"}
    assert mmr._get_param_names(return_alias=False) == {"foo"}
    assert mmr._get_param_names(return_alias=True) == {"bar"}