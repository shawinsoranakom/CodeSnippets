def test_config_mixin_3_multi_inheritance_not_override_config():
    """Test config mixin with multiple inheritance"""
    i = Config(llm=mock_llm_config)
    j = Config(llm=mock_llm_config_proxy)
    obj = ModelY(config=i)
    assert obj.config == i
    assert obj.config.llm == mock_llm_config

    obj.set_config(j)
    # obj already has a config, so it will not be set
    assert obj.config == i
    assert obj.config.llm == mock_llm_config

    assert obj.a == "a"
    assert obj.b == "b"
    assert obj.c == "c"
    assert obj.d == "d"

    print(obj.__dict__.keys())
    assert "private_config" in obj.__dict__.keys()