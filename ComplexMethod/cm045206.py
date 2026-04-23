def test_config_serialization(test_config: ComponentModel) -> None:
    tool = HttpTool.load_component(test_config)
    config = tool.dump_component()

    assert config.config["name"] == test_config.config["name"]
    assert config.config["description"] == test_config.config["description"]
    assert config.config["host"] == test_config.config["host"]
    assert config.config["port"] == test_config.config["port"]
    assert config.config["path"] == test_config.config["path"]
    assert config.config["scheme"] == test_config.config["scheme"]
    assert config.config["method"] == test_config.config["method"]
    assert config.config["headers"] == test_config.config["headers"]