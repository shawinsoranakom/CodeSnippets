def test_path_prefix_matching():
    """Test that path prefix matching works correctly."""
    middleware = SecurityHeadersMiddleware(Starlette())

    # Test that paths starting with cacheable prefixes are cacheable
    assert middleware.is_cacheable_path("/static/css/style.css")
    assert middleware.is_cacheable_path("/static/js/app.js")
    assert middleware.is_cacheable_path("/assets/images/logo.png")
    assert middleware.is_cacheable_path("/_next/static/chunks/main.js")

    # Test that other API paths are not cacheable by default
    assert not middleware.is_cacheable_path("/api/users/profile")
    assert not middleware.is_cacheable_path("/api/v1/private/data")
    assert not middleware.is_cacheable_path("/api/billing/subscription")