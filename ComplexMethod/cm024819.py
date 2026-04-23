def test_ssl_context_insecure_alpn_bucketing() -> None:
    """Test that INSECURE cipher list SSL contexts are bucketed by ALPN protocols.

    INSECURE cipher list is used by some integrations that need to connect to
    devices with outdated TLS implementations.
    """
    # HTTP/1.1, HTTP/2, and no-ALPN contexts should all be different
    http1_context = client_context(SSLCipherList.INSECURE, SSL_ALPN_HTTP11)
    http2_context = client_context(SSLCipherList.INSECURE, SSL_ALPN_HTTP11_HTTP2)
    no_alpn_context = client_context(SSLCipherList.INSECURE, SSL_ALPN_NONE)
    assert http1_context is not http2_context
    assert http1_context is not no_alpn_context
    assert http2_context is not no_alpn_context

    # Same parameters should return cached context
    assert client_context(SSLCipherList.INSECURE, SSL_ALPN_HTTP11) is http1_context
    assert (
        client_context(SSLCipherList.INSECURE, SSL_ALPN_HTTP11_HTTP2) is http2_context
    )
    assert client_context(SSLCipherList.INSECURE, SSL_ALPN_NONE) is no_alpn_context

    # No-verify contexts should also be bucketed by ALPN
    http1_no_verify = client_context_no_verify(SSLCipherList.INSECURE, SSL_ALPN_HTTP11)
    http2_no_verify = client_context_no_verify(
        SSLCipherList.INSECURE, SSL_ALPN_HTTP11_HTTP2
    )
    no_alpn_no_verify = client_context_no_verify(SSLCipherList.INSECURE, SSL_ALPN_NONE)
    assert http1_no_verify is not http2_no_verify
    assert http1_no_verify is not no_alpn_no_verify
    assert http2_no_verify is not no_alpn_no_verify

    # create_no_verify_ssl_context should also work with ALPN
    assert (
        create_no_verify_ssl_context(SSLCipherList.INSECURE, SSL_ALPN_HTTP11)
        is http1_no_verify
    )
    assert (
        create_no_verify_ssl_context(SSLCipherList.INSECURE, SSL_ALPN_HTTP11_HTTP2)
        is http2_no_verify
    )
    assert (
        create_no_verify_ssl_context(SSLCipherList.INSECURE, SSL_ALPN_NONE)
        is no_alpn_no_verify
    )