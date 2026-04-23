async def resolve_wxo_client_credentials(
    *,
    user_id: UUID | str,
    db: AsyncSession,
    provider_id: UUID,
) -> WxOCredentials:
    """Resolve Watsonx Orchestrate client credentials from deployment provider account.

    The decrypted API key is used only to instantiate the SDK authenticator and is not
    retained in adapter credential objects.
    """
    try:
        provider_account = await get_provider_account_by_id(
            db,
            provider_id=provider_id,
            user_id=user_id,
        )
        if provider_account is None:
            msg = "Failed to find deployment provider account credentials."
            raise CredentialResolutionError(message=msg)

        instance_url = (provider_account.provider_url or "").strip()
        api_key = auth_utils.decrypt_api_key((provider_account.api_key or "").strip())
        if not instance_url or not api_key:
            msg = "Watsonx Orchestrate backend URL and API key must be configured."
            raise CredentialResolutionError(message=msg)

    except CredentialResolutionError:
        raise
    except Exception as exc:
        msg = "An unexpected error occurred while resolving Watsonx Orchestrate client credentials."
        raise CredentialResolutionError(message=msg) from exc

    authenticator = get_authenticator(instance_url=instance_url, api_key=api_key)
    return WxOCredentials(instance_url=instance_url, authenticator=authenticator)