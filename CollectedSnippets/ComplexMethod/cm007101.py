def _build_embeddings(self, metadata: dict, *, api_key: str | None = None, provider_vars: dict | None = None):
        """Build embedding model from metadata.

        Args:
            metadata: The knowledge base embedding metadata.
            api_key: Pre-resolved API key (user override > metadata > global).
            provider_vars: Pre-resolved provider variables (for Ollama/WatsonX).
        """
        provider = metadata.get("embedding_provider")
        model = metadata.get("embedding_model")
        chunk_size = metadata.get("chunk_size")

        # Handle various providers
        if provider == "OpenAI":
            from langchain_openai import OpenAIEmbeddings

            if not api_key:
                msg = (
                    "OpenAI API key is required. Provide it in the component's advanced settings"
                    " or configure it globally."
                )
                raise ValueError(msg)
            openai_kwargs: dict = {"model": model, "api_key": api_key}
            if chunk_size is not None:
                openai_kwargs["chunk_size"] = chunk_size
            return OpenAIEmbeddings(**openai_kwargs)
        if provider == "HuggingFace":
            from langchain_huggingface import HuggingFaceEmbeddings

            return HuggingFaceEmbeddings(
                model=model,
            )
        if provider == "Cohere":
            from langchain_cohere import CohereEmbeddings

            if not api_key:
                msg = "Cohere API key is required when using Cohere provider"
                raise ValueError(msg)
            return CohereEmbeddings(
                model=model,
                cohere_api_key=api_key,
            )
        if provider == "Google Generative AI":
            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            if not api_key:
                msg = (
                    "Google API key is required. Provide it in the component's advanced settings"
                    " or configure it globally."
                )
                raise ValueError(msg)
            return GoogleGenerativeAIEmbeddings(
                model=model,
                google_api_key=api_key,
            )
        if provider == "Ollama":
            from langchain_ollama import OllamaEmbeddings

            all_vars = provider_vars or {}
            base_url = all_vars.get("OLLAMA_BASE_URL")
            kwargs: dict = {"model": model}
            if base_url:
                kwargs["base_url"] = base_url
            return OllamaEmbeddings(**kwargs)
        if provider == "IBM WatsonX":
            from langchain_ibm import WatsonxEmbeddings

            all_vars = provider_vars or {}
            watsonx_apikey = api_key or all_vars.get("WATSONX_APIKEY")
            watsonx_project_id = all_vars.get("WATSONX_PROJECT_ID")
            watsonx_url = all_vars.get("WATSONX_URL")
            if not watsonx_apikey:
                msg = (
                    "IBM WatsonX API key is required. Provide it in the component's advanced settings"
                    " or configure it globally."
                )
                raise ValueError(msg)
            kwargs = {"model_id": model, "apikey": watsonx_apikey}
            if watsonx_project_id:
                kwargs["project_id"] = watsonx_project_id
            if watsonx_url:
                kwargs["url"] = watsonx_url
            return WatsonxEmbeddings(**kwargs)
        if provider == "Custom":
            # For custom embedding models, we would need additional configuration
            msg = "Custom embedding models not yet supported"
            raise NotImplementedError(msg)
        msg = f"Embedding provider '{provider}' is not supported for retrieval."
        raise NotImplementedError(msg)