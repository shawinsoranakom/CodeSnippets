def test_provider_name_extraction(self, mock_api_key):
        """Test provider name extraction from model IDs."""
        discovery = GroqModelDiscovery(api_key=mock_api_key)

        # Models with slash notation
        assert discovery._get_provider_name("meta-llama/llama-3.1-8b") == "Meta"
        assert discovery._get_provider_name("openai/gpt-oss-safeguard-20b") == "OpenAI"
        assert discovery._get_provider_name("qwen/qwen3-32b") == "Alibaba Cloud"
        assert discovery._get_provider_name("moonshotai/moonshot-v1") == "Moonshot AI"
        assert discovery._get_provider_name("groq/groq-model") == "Groq"

        # Models with prefixes
        assert discovery._get_provider_name("llama-3.1-8b-instant") == "Meta"
        assert discovery._get_provider_name("llama3-70b-8192") == "Meta"
        assert discovery._get_provider_name("qwen-2.5-32b") == "Alibaba Cloud"
        assert discovery._get_provider_name("allam-1-13b") == "SDAIA"

        # Unknown providers default to Groq
        assert discovery._get_provider_name("unknown-model") == "Groq"