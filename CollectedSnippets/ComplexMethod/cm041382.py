def test_java_system_properties_proxy(monkeypatch):
    # Ensure various combinations of env config options are properly converted into expected sys props

    monkeypatch.setattr(config, "OUTBOUND_HTTP_PROXY", "http://lorem.com:69")
    monkeypatch.setattr(config, "OUTBOUND_HTTPS_PROXY", "")
    output = java.java_system_properties_proxy()
    assert len(output) == 2
    assert output["http.proxyHost"] == "lorem.com"
    assert output["http.proxyPort"] == "69"

    monkeypatch.setattr(config, "OUTBOUND_HTTP_PROXY", "")
    monkeypatch.setattr(config, "OUTBOUND_HTTPS_PROXY", "http://ipsum.com")
    output = java.java_system_properties_proxy()
    assert len(output) == 2
    assert output["https.proxyHost"] == "ipsum.com"
    assert output["https.proxyPort"] == "443"

    # Ensure no explicit port defaults to 80
    monkeypatch.setattr(config, "OUTBOUND_HTTP_PROXY", "http://baz.com")
    monkeypatch.setattr(config, "OUTBOUND_HTTPS_PROXY", "http://qux.com:42")
    output = java.java_system_properties_proxy()
    assert len(output) == 4
    assert output["http.proxyHost"] == "baz.com"
    assert output["http.proxyPort"] == "80"
    assert output["https.proxyHost"] == "qux.com"
    assert output["https.proxyPort"] == "42"