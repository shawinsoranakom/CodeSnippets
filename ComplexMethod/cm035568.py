def test_preserves_original_url_structure(self, mock_is_docker):
        """Test that all URL components are preserved correctly."""
        original_url = 'https://user:pass@localhost:8443/api/v1/endpoint?param1=value1&param2=value2#fragment'
        result = replace_localhost_hostname_for_docker(original_url)
        expected = 'https://user:pass@host.docker.internal:8443/api/v1/endpoint?param1=value1&param2=value2#fragment'

        assert result == expected

        # Verify each component is preserved
        from urllib.parse import urlparse

        original_parsed = urlparse(original_url)
        result_parsed = urlparse(result)

        assert original_parsed.scheme == result_parsed.scheme
        assert original_parsed.username == result_parsed.username
        assert original_parsed.password == result_parsed.password
        assert original_parsed.port == result_parsed.port
        assert original_parsed.path == result_parsed.path
        assert original_parsed.query == result_parsed.query
        assert original_parsed.fragment == result_parsed.fragment

        # Only hostname should be different
        assert original_parsed.hostname == 'localhost'
        assert result_parsed.hostname == 'host.docker.internal'