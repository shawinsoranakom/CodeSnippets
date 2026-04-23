def get_provider_tokens():
    """Retrieve provider tokens from environment variables and return them as a dictionary.

    Returns:
        A dictionary mapping ProviderType to ProviderToken if tokens are found, otherwise None.
    """
    # Collect provider tokens from environment variables if available
    provider_tokens = {}
    if 'GITHUB_TOKEN' in os.environ:
        github_token = SecretStr(os.environ['GITHUB_TOKEN'])
        provider_tokens[ProviderType.GITHUB] = ProviderToken(token=github_token)

    if 'GITLAB_TOKEN' in os.environ:
        gitlab_token = SecretStr(os.environ['GITLAB_TOKEN'])
        provider_tokens[ProviderType.GITLAB] = ProviderToken(token=gitlab_token)

    if 'BITBUCKET_TOKEN' in os.environ:
        bitbucket_token = SecretStr(os.environ['BITBUCKET_TOKEN'])
        provider_tokens[ProviderType.BITBUCKET] = ProviderToken(token=bitbucket_token)

    # Forgejo support (e.g., Codeberg or self-hosted Forgejo)
    if 'FORGEJO_TOKEN' in os.environ:
        forgejo_token = SecretStr(os.environ['FORGEJO_TOKEN'])
        # If a base URL is provided, extract the domain to use as host override
        forgejo_base_url = os.environ.get('FORGEJO_BASE_URL', '').strip()
        host: str | None = None
        if forgejo_base_url:
            # Normalize by stripping protocol and any path (e.g., /api/v1)
            url = forgejo_base_url
            if url.startswith(('http://', 'https://')):
                try:
                    from urllib.parse import urlparse

                    parsed = urlparse(url)
                    host = parsed.netloc or None
                except Exception:
                    pass
            if host is None:
                host = url.replace('https://', '').replace('http://', '')
            host = host.split('/')[0].strip('/') if host else None
        provider_tokens[ProviderType.FORGEJO] = ProviderToken(
            token=forgejo_token, host=host
        )

    # Wrap provider tokens in Secrets if any tokens were found
    secret_store = (
        Secrets(provider_tokens=provider_tokens) if provider_tokens else None  # type: ignore[arg-type]
    )
    return secret_store.provider_tokens if secret_store else None