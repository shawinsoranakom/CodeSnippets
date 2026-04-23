async def delete_credentials(
    request: Request,
    provider: Annotated[
        ProviderName, Path(title="The provider to delete credentials for")
    ],
    cred_id: Annotated[str, Path(title="The ID of the credentials to delete")],
    user_id: Annotated[str, Security(get_user_id)],
    force: Annotated[
        bool, Query(title="Whether to proceed if any linked webhooks are still in use")
    ] = False,
) -> CredentialsDeletionResponse | CredentialsDeletionNeedsConfirmationResponse:
    if is_sdk_default(cred_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Credentials not found"
        )
    if is_system_credential(cred_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System-managed credentials cannot be deleted",
        )
    creds = await creds_manager.store.get_creds_by_id(user_id, cred_id)
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Credentials not found"
        )
    if not provider_matches(creds.provider, provider):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credentials not found",
        )
    if creds.is_managed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AutoGPT-managed credentials cannot be deleted",
        )

    try:
        await remove_all_webhooks_for_credentials(user_id, creds, force)
    except NeedConfirmation as e:
        return CredentialsDeletionNeedsConfirmationResponse(message=str(e))

    await creds_manager.delete(user_id, cred_id)

    tokens_revoked = None
    if isinstance(creds, OAuth2Credentials):
        if provider_matches(provider.value, ProviderName.MCP.value):
            # MCP uses dynamic per-server OAuth — create handler from metadata
            handler = create_mcp_oauth_handler(creds)
        else:
            handler = _get_provider_oauth_handler(request, provider)
        tokens_revoked = await handler.revoke_tokens(creds)

    return CredentialsDeletionResponse(revoked=tokens_revoked)