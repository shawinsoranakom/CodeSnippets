def init_embeddings(
    model: str,
    *,
    provider: str | None = None,
    **kwargs: Any,
) -> Embeddings | Runnable[Any, list[float]]:
    """Initialize an embeddings model from a model name and optional provider.

    !!! note
        Must have the integration package corresponding to the model provider
        installed.

    Args:
        model: Name of the model to use.

            Can be either:

            - A model string like `"openai:text-embedding-3-small"`
            - Just the model name if the provider is specified separately or can be
                inferred.

            See supported providers under the `provider` arg description.
        provider: Optional explicit provider name. If not specified, will attempt to
            parse from the model string in the `model` arg.

            Supported providers:

            - `openai`                  -> [`langchain-openai`](https://docs.langchain.com/oss/python/integrations/providers/openai)
            - `azure_ai`                -> [`langchain-azure-ai`](https://docs.langchain.com/oss/python/integrations/providers/microsoft)
            - `azure_openai`            -> [`langchain-openai`](https://docs.langchain.com/oss/python/integrations/providers/openai)
            - `bedrock`                 -> [`langchain-aws`](https://docs.langchain.com/oss/python/integrations/providers/aws)
            - `cohere`                  -> [`langchain-cohere`](https://docs.langchain.com/oss/python/integrations/providers/cohere)
            - `google_genai`            -> [`langchain-google-genai`](https://docs.langchain.com/oss/python/integrations/providers/google)
            - `google_vertexai`         -> [`langchain-google-vertexai`](https://docs.langchain.com/oss/python/integrations/providers/google)
            - `huggingface`             -> [`langchain-huggingface`](https://docs.langchain.com/oss/python/integrations/providers/huggingface)
            - `mistralai`               -> [`langchain-mistralai`](https://docs.langchain.com/oss/python/integrations/providers/mistralai)
            - `ollama`                  -> [`langchain-ollama`](https://docs.langchain.com/oss/python/integrations/providers/ollama)

        **kwargs: Additional model-specific parameters passed to the embedding model.
            These vary by provider, see the provider-specific documentation for details.

    Returns:
        An `Embeddings` instance that can generate embeddings for text.

    Raises:
        ValueError: If the model provider is not supported or cannot be determined
        ImportError: If the required provider package is not installed

    ???+ note "Example Usage"

        ```python
        # Using a model string
        model = init_embeddings("openai:text-embedding-3-small")
        model.embed_query("Hello, world!")

        # Using explicit provider
        model = init_embeddings(model="text-embedding-3-small", provider="openai")
        model.embed_documents(["Hello, world!", "Goodbye, world!"])

        # With additional parameters
        model = init_embeddings("openai:text-embedding-3-small", api_key="sk-...")
        ```

    !!! version-added "Added in `langchain` 0.3.9"

    """
    if not model:
        providers = _SUPPORTED_PROVIDERS.keys()
        msg = (
            f"Must specify model name. Supported providers are: {', '.join(providers)}"
        )
        raise ValueError(msg)

    provider, model_name = _infer_model_and_provider(model, provider=provider)
    pkg = _SUPPORTED_PROVIDERS[provider]
    _check_pkg(pkg)

    if provider == "azure_ai":
        from langchain_azure_ai.embeddings import AzureAIOpenAIApiEmbeddingsModel

        return AzureAIOpenAIApiEmbeddingsModel(model=model_name, **kwargs)
    if provider == "azure_openai":
        from langchain_openai import AzureOpenAIEmbeddings

        return AzureOpenAIEmbeddings(model=model_name, **kwargs)
    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(model=model_name, **kwargs)
    if provider == "bedrock":
        from langchain_aws import BedrockEmbeddings

        return BedrockEmbeddings(model_id=model_name, **kwargs)
    if provider == "google_genai":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        return GoogleGenerativeAIEmbeddings(model=model_name, **kwargs)
    if provider == "google_vertexai":
        from langchain_google_vertexai import VertexAIEmbeddings

        return VertexAIEmbeddings(model=model_name, **kwargs)
    if provider == "cohere":
        from langchain_cohere import CohereEmbeddings

        return CohereEmbeddings(model=model_name, **kwargs)
    if provider == "mistralai":
        from langchain_mistralai import MistralAIEmbeddings

        return MistralAIEmbeddings(model=model_name, **kwargs)
    if provider == "huggingface":
        from langchain_huggingface import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(model_name=model_name, **kwargs)
    if provider == "ollama":
        from langchain_ollama import OllamaEmbeddings

        return OllamaEmbeddings(model=model_name, **kwargs)
    msg = (
        f"Provider '{provider}' is not supported.\n"
        f"Supported providers and their required packages:\n"
        f"{_get_provider_list()}"
    )
    raise ValueError(msg)