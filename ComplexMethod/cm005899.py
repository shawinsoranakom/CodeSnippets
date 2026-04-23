def test_should_build_config_for_openai(self):
        """Should build correct config for OpenAI provider."""
        result = _build_model_config("OpenAI", "gpt-4o-mini")

        assert len(result) == 1
        config = result[0]
        assert config["provider"] == "OpenAI"
        assert config["name"] == "gpt-4o-mini"
        assert config["icon"] == "OpenAI"
        assert config["metadata"]["model_class"] == "ChatOpenAI"
        assert config["metadata"]["model_name_param"] == "model"
        assert config["metadata"]["api_key_param"] == "api_key"