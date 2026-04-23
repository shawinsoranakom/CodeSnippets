def test_cacheable_endpoints_dont_have_cache_control_headers(client):
    """Test that explicitly cacheable endpoints don't have restrictive cache control headers."""
    cacheable_endpoints = [
        "/api/store/agents",
        "/api/health",
        "/static/logo.png",
    ]

    for endpoint in cacheable_endpoints:
        response = client.get(endpoint)

        # Should NOT have restrictive cache control headers
        assert (
            "Cache-Control" not in response.headers
            or "no-store" not in response.headers.get("Cache-Control", "")
        )
        assert (
            "Pragma" not in response.headers
            or response.headers.get("Pragma") != "no-cache"
        )
        assert (
            "Expires" not in response.headers or response.headers.get("Expires") != "0"
        )

        # Should still have general security headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"