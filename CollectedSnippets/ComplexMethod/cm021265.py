def test_client_id_hostname() -> None:
    """Test we enforce valid hostname."""
    assert indieauth._parse_client_id("http://www.home-assistant.io/")
    assert indieauth._parse_client_id("http://[::1]")
    assert indieauth._parse_client_id("http://127.0.0.1")
    assert indieauth._parse_client_id("http://10.0.0.0")
    assert indieauth._parse_client_id("http://10.255.255.255")
    assert indieauth._parse_client_id("http://172.16.0.0")
    assert indieauth._parse_client_id("http://172.31.255.255")
    assert indieauth._parse_client_id("http://192.168.0.0")
    assert indieauth._parse_client_id("http://192.168.255.255")

    with pytest.raises(ValueError):
        assert indieauth._parse_client_id("http://255.255.255.255/")
    with pytest.raises(ValueError):
        assert indieauth._parse_client_id("http://11.0.0.0/")
    with pytest.raises(ValueError):
        assert indieauth._parse_client_id("http://172.32.0.0/")
    with pytest.raises(ValueError):
        assert indieauth._parse_client_id("http://192.167.0.0/")