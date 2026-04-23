def test_basic_openrouter_env(self):
        cfg = self._openrouter_config()
        with patch("backend.copilot.sdk.env.config", cfg):
            from backend.copilot.sdk.env import build_sdk_env

            result = build_sdk_env()

        assert result["ANTHROPIC_BASE_URL"] == "https://openrouter.ai/api"
        assert result["ANTHROPIC_AUTH_TOKEN"] == "sk-or-test-key"
        assert result["ANTHROPIC_API_KEY"] == ""
        # SDK 0.1.58: Accept-Encoding: identity is always injected
        assert "ANTHROPIC_CUSTOM_HEADERS" in result
        assert "Accept-Encoding: identity" in result["ANTHROPIC_CUSTOM_HEADERS"]
        # OpenRouter compat: env var must always be present
        assert result.get("CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS") == "1"
        assert result.get("CLAUDE_AUTOCOMPACT_PCT_OVERRIDE") == "50"