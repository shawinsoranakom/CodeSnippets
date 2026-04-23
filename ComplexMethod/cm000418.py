def test_host_scoped_credentials_creation(self):
        """Test creating HostScopedCredentials with required fields."""
        creds = HostScopedCredentials(
            provider="custom",
            host="api.example.com",
            headers={
                "Authorization": SecretStr("Bearer secret-token"),
                "X-API-Key": SecretStr("api-key-123"),
            },
            title="Example API Credentials",
        )

        assert creds.type == "host_scoped"
        assert creds.provider == "custom"
        assert creds.host == "api.example.com"
        assert creds.title == "Example API Credentials"
        assert len(creds.headers) == 2
        assert "Authorization" in creds.headers
        assert "X-API-Key" in creds.headers