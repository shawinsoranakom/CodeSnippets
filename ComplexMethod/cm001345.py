async def assert_config_has_required_llm_api_keys(config: AppConfig) -> None:
    """
    Check if API keys (if required) are set for the configured SMART_LLM and FAST_LLM.
    """
    from pydantic import ValidationError

    from forge.llm.providers.anthropic import AnthropicModelName
    from forge.llm.providers.groq import GroqModelName

    if set((config.smart_llm, config.fast_llm)).intersection(AnthropicModelName):
        from forge.llm.providers.anthropic import AnthropicCredentials

        try:
            credentials = AnthropicCredentials.from_env()
        except ValidationError as e:
            if "api_key" in str(e):
                logger.error(
                    "Set your Anthropic API key in .env or as an environment variable"
                )
                logger.info(
                    "For further instructions: "
                    "https://docs.agpt.co/classic/original_autogpt/setup/#anthropic"
                )

            raise ValueError("Anthropic is unavailable: can't load credentials") from e

        key_pattern = r"^sk-ant-api03-[\w\-]{95}"

        # If key is set, but it looks invalid
        if not re.search(key_pattern, credentials.api_key.get_secret_value()):
            logger.warning(
                "Possibly invalid Anthropic API key! "
                f"Configured Anthropic API key does not match pattern '{key_pattern}'. "
                "If this is a valid key, please report this warning to the maintainers."
            )

    if set((config.smart_llm, config.fast_llm)).intersection(GroqModelName):
        from groq import AuthenticationError

        from forge.llm.providers.groq import GroqProvider

        try:
            groq = GroqProvider()
            await groq.get_available_models()
        except ValidationError as e:
            if "api_key" not in str(e):
                raise

            logger.error("Set your Groq API key in .env or as an environment variable")
            logger.info(
                "For further instructions: "
                + "https://docs.agpt.co/classic/original_autogpt/setup/#groq"
            )
            raise ValueError("Groq is unavailable: can't load credentials")
        except AuthenticationError as e:
            logger.error("The Groq API key is invalid!")
            logger.info(
                "For instructions to get and set a new API key: "
                "https://docs.agpt.co/classic/original_autogpt/setup/#groq"
            )
            raise ValueError("Groq is unavailable: invalid API key") from e

    if set((config.smart_llm, config.fast_llm)).intersection(OpenAIModelName):
        from openai import AuthenticationError

        from forge.llm.providers.openai import OpenAIProvider

        try:
            openai = OpenAIProvider()
            await openai.get_available_models()
        except ValidationError as e:
            if "api_key" not in str(e):
                raise

            logger.error(
                "Set your OpenAI API key in .env or as an environment variable"
            )
            logger.info(
                "For further instructions: "
                + "https://docs.agpt.co/classic/original_autogpt/setup/#openai"
            )
            raise ValueError("OpenAI is unavailable: can't load credentials")
        except AuthenticationError as e:
            logger.error("The OpenAI API key is invalid!")
            logger.info(
                "For instructions to get and set a new API key: "
                "https://docs.agpt.co/classic/original_autogpt/setup/#openai"
            )
            raise ValueError("OpenAI is unavailable: invalid API key") from e