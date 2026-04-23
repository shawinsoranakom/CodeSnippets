async def _get_provider_oauth_handler(provider_name_str: str) -> "BaseOAuthHandler":
    provider_name = ProviderName(provider_name_str)
    if provider_name not in HANDLERS_BY_NAME:
        raise KeyError(f"Unknown provider '{provider_name}'")

    provider_creds = CREDENTIALS_BY_PROVIDER[provider_name]
    if not provider_creds.use_secrets:
        # This is safe to do as we check that the env vars exist in the registry
        client_id = (
            os.getenv(provider_creds.client_id_env_var)
            if provider_creds.client_id_env_var
            else None
        )
        client_secret = (
            os.getenv(provider_creds.client_secret_env_var)
            if provider_creds.client_secret_env_var
            else None
        )
    else:
        client_id = getattr(settings.secrets, f"{provider_name.value}_client_id")
        client_secret = getattr(
            settings.secrets, f"{provider_name.value}_client_secret"
        )

    if not (client_id and client_secret):
        raise MissingConfigError(
            f"Integration with provider '{provider_name}' is not configured",
        )

    handler_class = HANDLERS_BY_NAME[provider_name]
    frontend_base_url = (
        settings.config.frontend_base_url or settings.config.platform_base_url
    )
    return handler_class(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=f"{frontend_base_url}/auth/integrations/oauth_callback",
    )