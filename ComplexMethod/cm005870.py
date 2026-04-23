def test_version_payload_serialization(self):
        """Test VersionPayload serialization to dictionary."""
        payload = VersionPayload(
            package="langflow",
            version="1.5.2",
            platform="macOS-12.0",
            python="3.10",
            arch="arm64",
            auto_login=True,
            cache_type="redis",
            backend_only=True,
            client_type="desktop",
        )

        data = payload.model_dump(by_alias=True)

        assert data["package"] == "langflow"
        assert data["version"] == "1.5.2"
        assert data["platform"] == "macOS-12.0"
        assert data["python"] == "3.10"
        assert data["arch"] == "arm64"
        assert data["autoLogin"] is True
        assert data["cacheType"] == "redis"
        assert data["backendOnly"] is True
        assert data["clientType"] == "desktop"