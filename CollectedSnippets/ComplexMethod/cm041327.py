def test_dynamic_allowed_cors_origins_different_ports(monkeypatch):
    # test dynamic allowed origins for default config (:4566)
    monkeypatch.setattr(config, "GATEWAY_LISTEN", default_gateway_listen)
    monkeypatch.setattr(cors, "_ALLOWED_INTERNAL_PORTS", cors._get_allowed_cors_ports())

    assert _origin_allowed("http://test.s3-website.localhost.localstack.cloud:4566")
    assert _origin_allowed("http://test.s3-website.localhost.localstack.cloud")
    assert _origin_allowed("https://test.s3-website.localhost.localstack.cloud:4566")
    assert _origin_allowed("https://test.s3-website.localhost.localstack.cloud")
    assert _origin_allowed("http://test.cloudfront.localhost.localstack.cloud")

    assert not _origin_allowed("https://test.cloudfront.localhost.localstack.cloud:443")
    assert not _origin_allowed("http://test.cloudfront.localhost.localstack.cloud:123")

    # test allowed origins for extended config (:4566,:443)
    monkeypatch.setattr(config, "GATEWAY_LISTEN", default_gateway_listen_ext)
    monkeypatch.setattr(cors, "_ALLOWED_INTERNAL_PORTS", cors._get_allowed_cors_ports())

    assert _origin_allowed("https://test.cloudfront.localhost.localstack.cloud:443")