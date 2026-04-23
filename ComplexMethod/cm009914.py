def _init_chat_model_helper(
    model: str,
    *,
    model_provider: str | None = None,
    **kwargs: Any,
) -> BaseChatModel:
    model, model_provider = _parse_model(model, model_provider)
    if model_provider == "openai":
        _check_pkg("langchain_openai", "ChatOpenAI")
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=model, **kwargs)
    if model_provider == "anthropic":
        _check_pkg("langchain_anthropic", "ChatAnthropic")
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=model, **kwargs)  # type: ignore[call-arg,unused-ignore]
    if model_provider == "azure_openai":
        _check_pkg("langchain_openai", "AzureChatOpenAI")
        from langchain_openai import AzureChatOpenAI

        return AzureChatOpenAI(model=model, **kwargs)
    if model_provider == "azure_ai":
        _check_pkg("langchain_azure_ai", "AzureAIOpenAIApiChatModel")
        from langchain_azure_ai.chat_models import AzureAIOpenAIApiChatModel

        return AzureAIOpenAIApiChatModel(model=model, **kwargs)
    if model_provider == "cohere":
        _check_pkg("langchain_cohere", "ChatCohere")
        from langchain_cohere import ChatCohere

        return ChatCohere(model=model, **kwargs)
    if model_provider == "google_vertexai":
        _check_pkg("langchain_google_vertexai", "ChatVertexAI")
        from langchain_google_vertexai import ChatVertexAI

        return ChatVertexAI(model=model, **kwargs)
    if model_provider == "google_genai":
        _check_pkg("langchain_google_genai", "ChatGoogleGenerativeAI")
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(model=model, **kwargs)
    if model_provider == "fireworks":
        _check_pkg("langchain_fireworks", "ChatFireworks")
        from langchain_fireworks import ChatFireworks

        return ChatFireworks(model=model, **kwargs)
    if model_provider == "ollama":
        try:
            _check_pkg("langchain_ollama", "ChatOllama")
            from langchain_ollama import ChatOllama
        except ImportError:
            # For backwards compatibility
            try:
                _check_pkg("langchain_community", "ChatOllama")
                from langchain_community.chat_models import ChatOllama
            except ImportError:
                # If both langchain-ollama and langchain-community aren't available,
                # raise an error related to langchain-ollama
                _check_pkg("langchain_ollama", "ChatOllama")

        return ChatOllama(model=model, **kwargs)
    if model_provider == "together":
        _check_pkg("langchain_together", "ChatTogether")
        from langchain_together import ChatTogether

        return ChatTogether(model=model, **kwargs)
    if model_provider == "mistralai":
        _check_pkg("langchain_mistralai", "ChatMistralAI")
        from langchain_mistralai import ChatMistralAI

        return ChatMistralAI(model=model, **kwargs)  # type: ignore[call-arg,unused-ignore]

    if model_provider == "huggingface":
        _check_pkg("langchain_huggingface", "ChatHuggingFace")
        from langchain_huggingface import ChatHuggingFace

        return ChatHuggingFace.from_model_id(model_id=model, **kwargs)

    if model_provider == "groq":
        _check_pkg("langchain_groq", "ChatGroq")
        from langchain_groq import ChatGroq

        return ChatGroq(model=model, **kwargs)
    if model_provider == "bedrock":
        _check_pkg("langchain_aws", "ChatBedrock")
        from langchain_aws import ChatBedrock

        # TODO: update to use model= once ChatBedrock supports
        return ChatBedrock(model_id=model, **kwargs)
    if model_provider == "bedrock_converse":
        _check_pkg("langchain_aws", "ChatBedrockConverse")
        from langchain_aws import ChatBedrockConverse

        return ChatBedrockConverse(model=model, **kwargs)
    if model_provider == "google_anthropic_vertex":
        _check_pkg("langchain_google_vertexai", "ChatAnthropicVertex")
        from langchain_google_vertexai.model_garden import ChatAnthropicVertex

        return ChatAnthropicVertex(model=model, **kwargs)
    if model_provider == "deepseek":
        _check_pkg("langchain_deepseek", "ChatDeepSeek", pkg_kebab="langchain-deepseek")
        from langchain_deepseek import ChatDeepSeek

        return ChatDeepSeek(model=model, **kwargs)
    if model_provider == "nvidia":
        _check_pkg("langchain_nvidia_ai_endpoints", "ChatNVIDIA")
        from langchain_nvidia_ai_endpoints import ChatNVIDIA

        return ChatNVIDIA(model=model, **kwargs)
    if model_provider == "ibm":
        _check_pkg("langchain_ibm", "ChatWatsonx")
        from langchain_ibm import ChatWatsonx

        return ChatWatsonx(model_id=model, **kwargs)
    if model_provider == "xai":
        _check_pkg("langchain_xai", "ChatXAI")
        from langchain_xai import ChatXAI

        return ChatXAI(model=model, **kwargs)
    if model_provider == "perplexity":
        _check_pkg("langchain_perplexity", "ChatPerplexity")
        from langchain_perplexity import ChatPerplexity

        return ChatPerplexity(model=model, **kwargs)
    if model_provider == "upstage":
        _check_pkg("langchain_upstage", "ChatUpstage")
        from langchain_upstage import ChatUpstage

        return ChatUpstage(model=model, **kwargs)
    supported = ", ".join(_SUPPORTED_PROVIDERS)
    msg = (
        f"Unsupported {model_provider=}.\n\nSupported model providers are: {supported}"
    )
    raise ValueError(msg)