def test_sets_env_vars_when_langfuse_configured(self):
        """OTEL env vars should be set when Langfuse credentials exist."""
        mock_settings = MagicMock()
        mock_settings.secrets.langfuse_public_key = "pk-test-123"
        mock_settings.secrets.langfuse_secret_key = "sk-test-456"
        mock_settings.secrets.langfuse_host = "https://langfuse.example.com"
        mock_settings.secrets.langfuse_tracing_environment = "test"

        with (
            patch(
                "backend.copilot.sdk.service._is_langfuse_configured",
                return_value=True,
            ),
            patch("backend.copilot.sdk.service.Settings", return_value=mock_settings),
            patch(
                "backend.copilot.sdk.service.configure_claude_agent_sdk",
                return_value=True,
            ) as mock_configure,
        ):
            from backend.copilot.sdk.service import _setup_langfuse_otel

            # Clear env vars so setdefault works
            env_keys = [
                "LANGSMITH_OTEL_ENABLED",
                "LANGSMITH_OTEL_ONLY",
                "LANGSMITH_TRACING",
                "OTEL_EXPORTER_OTLP_ENDPOINT",
                "OTEL_EXPORTER_OTLP_HEADERS",
                "OTEL_RESOURCE_ATTRIBUTES",
            ]
            saved = {k: os.environ.pop(k, None) for k in env_keys}
            try:
                _setup_langfuse_otel()

                assert os.environ["LANGSMITH_OTEL_ENABLED"] == "true"
                assert os.environ["LANGSMITH_OTEL_ONLY"] == "true"
                assert os.environ["LANGSMITH_TRACING"] == "true"
                assert (
                    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"]
                    == "https://langfuse.example.com/api/public/otel"
                )
                assert "Authorization=Basic" in os.environ["OTEL_EXPORTER_OTLP_HEADERS"]
                assert (
                    os.environ["OTEL_RESOURCE_ATTRIBUTES"]
                    == "langfuse.environment=test"
                )

                mock_configure.assert_called_once_with(tags=["sdk"])
            finally:
                for k, v in saved.items():
                    if v is not None:
                        os.environ[k] = v
                    elif k in os.environ:
                        del os.environ[k]