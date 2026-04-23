def test_allowed_cors_origins_different_ports_and_protocols(monkeypatch):
    # test allowed origins for default config (:4566)
    # GATEWAY_LISTEN binds each host-port configuration to both protocols (http and https)
    monkeypatch.setattr(config, "GATEWAY_LISTEN", default_gateway_listen)
    origins = cors._get_allowed_cors_origins()
    assert "http://localhost:4566" in origins
    assert "http://localhost.localstack.cloud:4566" in origins
    assert "http://localhost:433" not in origins
    assert "https://localhost.localstack.cloud:443" not in origins

    # test allowed origins for extended config (:4566,:443)
    monkeypatch.setattr(config, "GATEWAY_LISTEN", default_gateway_listen_ext)
    origins = cors._get_allowed_cors_origins()
    assert "http://localhost:4566" in origins
    assert "http://localhost:443" in origins
    assert "http://localhost.localstack.cloud:4566" in origins
    assert "https://localhost.localstack.cloud:443" in origins