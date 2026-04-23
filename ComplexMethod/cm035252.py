async def store_provider_tokens(
    provider_info: POSTProviderModel,
    secrets_store: SecretsStore = Depends(get_secrets_store),
    provider_tokens: PROVIDER_TOKEN_TYPE | None = Depends(get_provider_tokens),
) -> EditResponse:
    """Store git provider tokens.

    Saves the git provider tokens (GitHub, GitLab, Bitbucket, etc.) for the authenticated user.

    Returns:
        200: Git providers stored successfully
        401: Invalid token
        500: Error storing git providers
    """
    await check_provider_tokens(provider_info, provider_tokens)

    user_secrets = await secrets_store.load()
    if not user_secrets:
        user_secrets = Secrets()

    if provider_info.provider_tokens:
        existing_providers = [provider for provider in user_secrets.provider_tokens]

        # Merge incoming settings store with the existing one
        for provider, token_value in list(provider_info.provider_tokens.items()):
            if provider in existing_providers and not token_value.token:
                existing_token = user_secrets.provider_tokens.get(provider)
                if existing_token and existing_token.token:
                    provider_info.provider_tokens[provider] = existing_token

            provider_info.provider_tokens[provider] = provider_info.provider_tokens[
                provider
            ].model_copy(update={'host': token_value.host})

    updated_secrets = user_secrets.model_copy(
        update={'provider_tokens': provider_info.provider_tokens}
    )
    await secrets_store.store(updated_secrets)

    return EditResponse(
        message='Git providers stored',
    )