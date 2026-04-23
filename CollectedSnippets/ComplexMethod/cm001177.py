def test_non_cacheable_endpoints_have_cache_control_headers(client):
    """Test that non-cacheable endpoints (most endpoints) have proper cache control headers."""
    non_cacheable_endpoints = [
        "/api/auth/user",
        "/api/v1/integrations/oauth/google",
        "/api/graphs/123/execute",
        "/api/integrations/credentials",
    ]

    for endpoint in non_cacheable_endpoints:
        response = client.get(endpoint)

        # Check cache control headers are present (default behavior)
        assert (
            response.headers["Cache-Control"]
            == "no-store, no-cache, must-revalidate, private"
        )
        assert response.headers["Pragma"] == "no-cache"
        assert response.headers["Expires"] == "0"

        # Check general security headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"