def test_config_mixin_4_multi_inheritance_override_config():
    """Test config mixin with multiple inheritance"""
    i = Config(llm=mock_llm_config)
    j = Config(llm=mock_llm_config_zhipu)
    obj = ModelY(config=i)
    assert obj.config == i
    assert obj.config.llm == mock_llm_config

    obj.set_config(j, override=True)
    # override obj.config
    assert obj.config == j
    assert obj.config.llm == mock_llm_config_zhipu

    assert obj.a == "a"
    assert obj.b == "b"
    assert obj.c == "c"
    assert obj.d == "d"

    print(obj.__dict__.keys())
    assert "private_config" in obj.__dict__.keys()
    assert obj.config.llm.model == "mock_zhipu_model"