def test_ssl_context_cipher_bucketing() -> None:
    """Test that SSL contexts are bucketed by cipher list."""
    default_ctx = client_context(SSLCipherList.PYTHON_DEFAULT)
    modern_ctx = client_context(SSLCipherList.MODERN)
    intermediate_ctx = client_context(SSLCipherList.INTERMEDIATE)
    insecure_ctx = client_context(SSLCipherList.INSECURE)

    # Different cipher lists should return different contexts
    assert default_ctx is not modern_ctx
    assert default_ctx is not intermediate_ctx
    assert default_ctx is not insecure_ctx
    assert modern_ctx is not intermediate_ctx
    assert modern_ctx is not insecure_ctx
    assert intermediate_ctx is not insecure_ctx

    # Same parameters should return cached context
    assert client_context(SSLCipherList.PYTHON_DEFAULT) is default_ctx
    assert client_context(SSLCipherList.MODERN) is modern_ctx