async def test_url_validation_function(self):
        """Test URL validation with valid and invalid URLs."""
        client = MCPStreamableHttpClient()

        # Test valid HTTPS URL
        is_valid, error = await client.validate_url("https://example.com/mcp")
        assert is_valid is True
        assert error == ""

        # Test valid HTTP URL
        is_valid, error = await client.validate_url("http://localhost:8080/mcp")
        assert is_valid is True
        assert error == ""

        # Test invalid URL format
        is_valid, error = await client.validate_url("not_a_url")
        assert is_valid is False
        assert "Invalid URL format" in error

        # Test URL without scheme
        is_valid, error = await client.validate_url("example.com/mcp")
        assert is_valid is False
        assert "Invalid URL format" in error