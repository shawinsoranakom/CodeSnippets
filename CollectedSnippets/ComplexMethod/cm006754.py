def convert_llm(llm: Any, excluded_keys=None):
    """Converts a LangChain LLM object to a CrewAI-compatible LLM object.

    Args:
        llm: A LangChain LLM object.
        excluded_keys: A set of keys to exclude from the conversion.

    Returns:
        A CrewAI-compatible LLM object
    """
    try:
        from crewai import LLM
    except ImportError as e:
        msg = "CrewAI is not installed. Please install it with `uv pip install crewai`."
        raise ImportError(msg) from e

    if not llm:
        return None

    # Check if this is already an LLM object
    if isinstance(llm, LLM):
        return llm

    # Check if we should use model_name model, or something else
    if hasattr(llm, "model_name") and llm.model_name:
        model_name = llm.model_name
    elif hasattr(llm, "model") and llm.model:
        model_name = llm.model
    elif hasattr(llm, "deployment_name") and llm.deployment_name:
        model_name = llm.deployment_name
    else:
        msg = "Could not find model name in the LLM object"
        raise ValueError(msg)

    # Normalize to the LLM model name
    # Remove langchain_ prefix if present
    provider = llm.get_lc_namespace()[0]
    api_base = None
    if provider.startswith("langchain_"):
        provider = provider[10:]
        model_name = f"{provider}/{model_name}"
    elif hasattr(llm, "azure_endpoint"):
        api_base = llm.azure_endpoint
        model_name = f"azure/{model_name}"

    # Retrieve the API Key from the LLM
    if excluded_keys is None:
        excluded_keys = {"model", "model_name", "_type", "api_key", "azure_deployment"}

    # Find the API key in the LLM
    api_key = _find_api_key(llm)

    # Convert Langchain LLM to CrewAI-compatible LLM object
    return LLM(
        model=model_name,
        api_key=api_key,
        api_base=api_base,
        **{k: v for k, v in llm.dict().items() if k not in excluded_keys},
    )