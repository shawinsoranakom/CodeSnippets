def test_config_deserialization(test_config: ComponentModel) -> None:
    tool = HttpTool.load_component(test_config)

    assert tool.name == test_config.config["name"]
    assert tool.description == test_config.config["description"]
    assert tool.server_params.host == test_config.config["host"]
    assert tool.server_params.port == test_config.config["port"]
    assert tool.server_params.path == test_config.config["path"]
    assert tool.server_params.scheme == test_config.config["scheme"]
    assert tool.server_params.method == test_config.config["method"]
    assert tool.server_params.headers == test_config.config["headers"]