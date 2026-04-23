def test_openai_proxy() -> None:
    """Test ChatOpenAI with proxy."""
    chat_openai = ChatOpenAI(openai_proxy="http://localhost:8080")
    mounts = chat_openai.client._client._client._mounts
    assert len(mounts) == 1
    for value in mounts.values():
        proxy = value._pool._proxy_url.origin
        assert proxy.scheme == b"http"
        assert proxy.host == b"localhost"
        assert proxy.port == 8080

    async_client_mounts = chat_openai.async_client._client._client._mounts
    assert len(async_client_mounts) == 1
    for value in async_client_mounts.values():
        proxy = value._pool._proxy_url.origin
        assert proxy.scheme == b"http"
        assert proxy.host == b"localhost"
        assert proxy.port == 8080