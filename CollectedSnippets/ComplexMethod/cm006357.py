async def update_provider_account(
    db: AsyncSession,
    *,
    provider_account: DeploymentProviderAccount,
    name: str | None = None,
    provider_tenant_id: str | None = _UNSET,  # type: ignore[assignment]
    provider_key: str | DeploymentProviderKey | None = None,
    provider_url: str | None = None,
    api_key: str | None = None,
) -> DeploymentProviderAccount:
    if name is not None:
        provider_account.name = _strip_or_raise(name, "name")
    if provider_tenant_id is not _UNSET:
        provider_account.provider_tenant_id = normalize_string_or_none(provider_tenant_id)  # type: ignore[arg-type]
    if provider_key is not None:
        provider_account.provider_key = _coerce_provider_key(provider_key)
    if provider_url is not None:
        provider_account.provider_url = _strip_or_raise(provider_url, "provider_url")
    if api_key is not None:
        try:
            provider_account.api_key = _encrypt_api_key(api_key)
        except RuntimeError:
            await logger.aerror(
                "Encryption failed updating provider account id=%s",
                provider_account.id,
            )
            raise
    provider_account.updated_at = datetime.now(timezone.utc)
    db.add(provider_account)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        await logger.aerror("IntegrityError updating provider account id=%s", provider_account.id)
        msg = "Provider account update conflicts with an existing record"
        raise ValueError(msg) from exc
    await db.refresh(provider_account)
    return provider_account