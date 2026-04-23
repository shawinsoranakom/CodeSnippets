def test_version_payload_initialization(self):
        """Test VersionPayload initialization with valid parameters."""
        payload = VersionPayload(
            package="langflow",
            version="1.0.0",
            platform="Linux-5.4.0",
            python="3.9",
            arch="x86_64",
            auto_login=False,
            cache_type="memory",
            backend_only=False,
            client_type="oss",
        )

        assert payload.package == "langflow"
        assert payload.version == "1.0.0"
        assert payload.platform == "Linux-5.4.0"
        assert payload.python == "3.9"
        assert payload.arch == "x86_64"
        assert payload.auto_login is False
        assert payload.cache_type == "memory"
        assert payload.backend_only is False
        assert payload.client_type == "oss"