def test_is_cacheable_path_detection():
    """Test the path detection logic."""
    middleware = SecurityHeadersMiddleware(Starlette())

    # Test cacheable paths (allow list)
    assert middleware.is_cacheable_path("/api/health")
    assert middleware.is_cacheable_path("/api/v1/health")
    assert middleware.is_cacheable_path("/static/image.png")
    assert middleware.is_cacheable_path("/api/store/agents")
    assert middleware.is_cacheable_path("/docs")
    assert middleware.is_cacheable_path("/favicon.ico")

    # Test non-cacheable paths (everything else)
    assert not middleware.is_cacheable_path("/api/auth/user")
    assert not middleware.is_cacheable_path("/api/v1/integrations/oauth/callback")
    assert not middleware.is_cacheable_path("/api/integrations/credentials/123")
    assert not middleware.is_cacheable_path("/api/graphs/abc123/execute")
    assert not middleware.is_cacheable_path("/api/store/xyz/submissions")