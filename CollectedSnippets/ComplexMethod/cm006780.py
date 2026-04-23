def validate_model_provider_key(provider: str, variables: dict[str, str], model_name: str | None = None) -> None:
    """Validate a model provider by making a minimal test call."""
    if not provider:
        return

    first_model = None
    try:
        from .model_catalog import get_unified_models_detailed

        models = get_unified_models_detailed(providers=[provider])
        if models and models[0].get("models"):
            first_model = models[0]["models"][0]["model_name"]
    except Exception as e:  # noqa: BLE001
        logger.error(f"Error getting unified models for provider {provider}: {e}")

    # For providers that need a model to test credentials
    if not first_model and provider in [
        "OpenAI",
        "Anthropic",
        "Google Generative AI",
        "IBM WatsonX",
    ]:
        return

    try:
        if provider == "OpenAI":
            from langchain_openai import ChatOpenAI  # type: ignore  # noqa: PGH003

            api_key = variables.get("OPENAI_API_KEY")
            if not api_key:
                return
            llm = ChatOpenAI(api_key=api_key, model_name=first_model, max_tokens=1)
            llm.invoke("test")

        elif provider == "Anthropic":
            from langchain_anthropic import ChatAnthropic  # type: ignore  # noqa: PGH003

            api_key = variables.get("ANTHROPIC_API_KEY")
            if not api_key:
                return
            llm = ChatAnthropic(anthropic_api_key=api_key, model=first_model, max_tokens=1)
            llm.invoke("test")

        elif provider == "Google Generative AI":
            from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore  # noqa: PGH003

            api_key = variables.get("GOOGLE_API_KEY")
            if not api_key:
                return
            llm = ChatGoogleGenerativeAI(google_api_key=api_key, model=first_model, max_tokens=1)
            llm.invoke("test")

        elif provider == "IBM WatsonX":
            from langchain_ibm import ChatWatsonx

            api_key = variables.get("WATSONX_APIKEY")
            project_id = variables.get("WATSONX_PROJECT_ID")
            url = variables.get("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
            if not api_key or not project_id:
                return
            llm = ChatWatsonx(
                apikey=api_key,
                url=url,
                model_id=first_model,
                project_id=project_id,
                params={"max_new_tokens": 1},
            )
            llm.invoke("test")

        elif provider == "Ollama":
            import requests

            base_url = variables.get("OLLAMA_BASE_URL")
            if not base_url:
                msg = "Invalid Ollama base URL"
                logger.error(msg)
                raise ValueError(msg)

            base_url = base_url.rstrip("/")
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            response.raise_for_status()

            data = response.json()
            if not isinstance(data, dict) or "models" not in data:
                msg = "Invalid Ollama base URL"
                logger.error(msg)
                raise ValueError(msg)

            if model_name:
                available_models = [m.get("name") for m in data["models"]]
                # Exact match or match with :latest
                if model_name not in available_models and f"{model_name}:latest" not in available_models:
                    # Lenient check for missing tag
                    if ":" not in model_name:
                        if not any(m.startswith(f"{model_name}:") for m in available_models):
                            available_str = ", ".join(available_models[:3])
                            msg = f"Model '{model_name}' not found on Ollama server. Available: {available_str}"
                            logger.error(msg)
                            raise ValueError(msg)
                    else:
                        available_str = ", ".join(available_models[:3])
                        msg = f"Model '{model_name}' not found on Ollama server. Available: {available_str}"
                        logger.error(msg)
                        raise ValueError(msg)

    except ValueError:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if any(word in error_msg for word in ["401", "authentication", "api key"]):
            msg = f"Invalid API key for {provider}"
            logger.error(f"Invalid API key for {provider}: {e}")
            raise ValueError(msg) from e

        # Rethrow specific Ollama errors with a user-facing message
        if provider == "Ollama":
            msg = "Invalid Ollama base URL"
            logger.error(msg)
            raise ValueError(msg) from e

        # For others, log and return (allow saving despite minor errors)
        return