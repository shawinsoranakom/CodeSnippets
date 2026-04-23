def _get_oauth_handler_for_external(
    provider_name: str, redirect_uri: str
) -> "BaseOAuthHandler":
    """Get an OAuth handler configured with an external redirect URI."""
    # Ensure blocks are loaded so SDK providers are available
    try:
        from backend.blocks import load_all_blocks

        load_all_blocks()
    except Exception as e:
        logger.warning(f"Failed to load blocks: {e}")

    if provider_name not in HANDLERS_BY_NAME:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider_name}' does not support OAuth",
        )

    # Check if this provider has custom OAuth credentials
    oauth_credentials = CREDENTIALS_BY_PROVIDER.get(provider_name)

    if oauth_credentials and not oauth_credentials.use_secrets:
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
        client_id = getattr(settings.secrets, f"{provider_name}_client_id", None)
        client_secret = getattr(
            settings.secrets, f"{provider_name}_client_secret", None
        )

    if not (client_id and client_secret):
        logger.error(f"Attempt to use unconfigured {provider_name} OAuth integration")
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "message": f"Integration with provider '{provider_name}' is not configured.",
                "hint": "Set client ID and secret in the application's deployment environment",
            },
        )

    handler_class = HANDLERS_BY_NAME[provider_name]
    return handler_class(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
    )