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
    creds = await creds_manager.store.get_creds_by_id(user_id, cred_id)
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Credentials not found"
        )
    if creds.provider != provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credentials do not match the specified provider",
        )

    try:
        await remove_all_webhooks_for_credentials(user_id, creds, force)
    except NeedConfirmation as e:
        return CredentialsDeletionNeedsConfirmationResponse(message=str(e))

    await creds_manager.delete(user_id, cred_id)

    tokens_revoked = None
    if isinstance(creds, OAuth2Credentials):
        handler = _get_provider_oauth_handler(request, provider)
        tokens_revoked = await handler.revoke_tokens(creds)

    return CredentialsDeletionResponse(revoked=tokens_revoked)
