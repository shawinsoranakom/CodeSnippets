def resolve_provider_llm_base_url(
    model: str | None,
    base_url: str | None,
    provider_base_url: str | None = None,
) -> str | None:
    """Apply deployment-specific LLM proxy override when needed.

    When the model uses ``openhands/`` or ``litellm_proxy/`` prefix and the
    stored ``base_url`` is the SDK default, replace it with the deployment's
    provider URL.

    Priority: user-explicit URL > deployment provider URL > SDK default.

    Args:
        model: LLM model name (e.g. ``litellm_proxy/gpt-4``).
        base_url: The base URL from user/org settings.
        provider_base_url: Deployment provider URL.  Falls back to
            ``get_openhands_provider_base_url()`` when *None*.
    """
    if not model or not (
        model.startswith('openhands/') or model.startswith('litellm_proxy/')
    ):
        return base_url

    user_set_custom = base_url and base_url.rstrip('/') != _SDK_DEFAULT_PROXY.rstrip(
        '/'
    )
    if user_set_custom:
        return base_url

    if provider_base_url is None:
        provider_base_url = get_openhands_provider_base_url()
    if provider_base_url:
        return provider_base_url

    return base_url