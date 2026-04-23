def test_normalize_url() -> None:
    """Test the normalizing of URLs."""
    assert network_util.normalize_url("http://example.com") == "http://example.com"
    assert network_util.normalize_url("https://example.com") == "https://example.com"
    assert network_util.normalize_url("https://example.com/") == "https://example.com"
    assert (
        network_util.normalize_url("https://example.com:443") == "https://example.com"
    )
    assert network_util.normalize_url("http://example.com:80") == "http://example.com"
    assert (
        network_util.normalize_url("https://example.com:80") == "https://example.com:80"
    )
    assert (
        network_util.normalize_url("http://example.com:443") == "http://example.com:443"
    )
    assert (
        network_util.normalize_url("https://example.com:443/test/")
        == "https://example.com/test"
    )
    assert network_util.normalize_url("/test/") == "/test"