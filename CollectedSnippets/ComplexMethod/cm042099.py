def test_proxy():
    assert _requests_proxies_arg(proxy=None) is None

    proxy = "127.0.0.1:80"
    assert _requests_proxies_arg(proxy=proxy) == {"http": proxy, "https": proxy}
    proxy_dict = {"http": proxy}
    assert _requests_proxies_arg(proxy=proxy_dict) == proxy_dict
    assert _aiohttp_proxies_arg(proxy_dict) == proxy
    proxy_dict = {"https": proxy}
    assert _requests_proxies_arg(proxy=proxy_dict) == proxy_dict
    assert _aiohttp_proxies_arg(proxy_dict) == proxy

    assert _make_session() is not None

    assert _aiohttp_proxies_arg(None) is None
    assert _aiohttp_proxies_arg("test") == "test"
    with pytest.raises(ValueError):
        _aiohttp_proxies_arg(-1)