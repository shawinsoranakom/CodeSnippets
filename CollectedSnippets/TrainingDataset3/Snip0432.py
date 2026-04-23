def _get_provider_oauth_handler(
    req: Request, provider_name: ProviderName
) -> "BaseOAuthHandler":
    # Ensure blocks are loaded so SDK providers are available
    try:
        from backend.blocks import load_all_blocks

        load_all_blocks()  # This is cached, so it only runs once
    except Exception as e:
        logger.warning(f"Failed to load blocks: {e}")

    # Convert provider_name to string for lookup
    provider_key = (
        provider_name.value if hasattr(provider_name, "value") else str(provider_name)
    )

    if provider_key not in HANDLERS_BY_NAME:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider_key}' does not support OAuth",
        )

    # Check if this provider has custom OAuth credentials
    oauth_credentials = CREDENTIALS_BY_PROVIDER.get(provider_key)

    if oauth_credentials and not oauth_credentials.use_secrets:
        # SDK provider with custom env vars
        import os

        client_id = (
            os.getenv(oauth_credentials.client_id_env_var)
            if oauth_credentials.client_id_env_var
            else None
        )
        client_secret = (
            os.getenv(oauth_credentials.client_secret_env_var)
            if oauth_credentials.client_secret_env_var
            else None
        )
    else:
        # Original provider using settings.secrets
        client_id = getattr(settings.secrets, f"{provider_name.value}_client_id", None)
        client_secret = getattr(
            settings.secrets, f"{provider_name.value}_client_secret", None
        )

    if not (client_id and client_secret):
        logger.error(
            f"Attempt to use unconfigured {provider_name.value} OAuth integration"
        )
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": f"Integration with provider '{provider_name.value}' is not configured.",
                "hint": "Set client ID and secret in the application's deployment environment",
            },
        )

    handler_class = HANDLERS_BY_NAME[provider_key]
    frontend_base_url = settings.config.frontend_base_url

    if not frontend_base_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Frontend base URL is not configured",
        )

    return handler_class(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=f"{frontend_base_url}/auth/integrations/oauth_callback",
    )
