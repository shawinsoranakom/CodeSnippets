def test_version_payload_creation_and_serialization(self):
        """Test VersionPayload creation and serialization."""
        payload = VersionPayload(
            package="langflow",
            version="1.5.0",
            platform="macOS-14.0-arm64",
            python="3.11",
            arch="64bit",
            auto_login=False,
            cache_type="redis",
            backend_only=True,
            client_type="oss",
        )

        assert payload.package == "langflow"
        assert payload.version == "1.5.0"
        assert payload.platform == "macOS-14.0-arm64"
        assert payload.python == "3.11"
        assert payload.arch == "64bit"
        assert payload.auto_login is False
        assert payload.cache_type == "redis"
        assert payload.backend_only is True

        serialized = payload.model_dump(by_alias=True)
        expected = {
            "package": "langflow",
            "version": "1.5.0",
            "platform": "macOS-14.0-arm64",
            "python": "3.11",
            "arch": "64bit",
            "autoLogin": False,
            "cacheType": "redis",
            "backendOnly": True,
            "clientType": "oss",
        }
        assert serialized == expected