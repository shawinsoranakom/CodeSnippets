def test_validate_url(self):
        """Test URL validation."""
        component = WebSearchComponent()

        # Valid URLs
        assert component.validate_url("https://example.com")
        assert component.validate_url("http://example.com")
        assert component.validate_url("www.example.com")
        assert component.validate_url("example.com")
        assert component.validate_url("https://subdomain.example.co.uk")

        # Invalid URLs
        assert not component.validate_url("not a url at all")
        assert not component.validate_url("://missing-protocol")