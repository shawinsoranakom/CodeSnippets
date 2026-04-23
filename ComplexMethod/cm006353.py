async def _check_key_from_db(session: AsyncSession, api_key: str, settings_service) -> User | None:
    """Validate API key against the database.

    Uses hash-based O(1) lookup first. Falls back to decrypt-and-compare
    for legacy keys that don't have a hash yet, and backfills the hash on match.
    """
    if not api_key:
        return None

    incoming_hash = hash_api_key(api_key)

    # Fast path: O(1) indexed lookup by hash
    query = select(ApiKey).where(ApiKey.api_key_hash == incoming_hash)
    matches = (await session.exec(query)).all()

    if len(matches) == 1:
        api_key_obj = matches[0]
        if settings_service.settings.disable_track_apikey_usage is not True:
            api_key_obj.total_uses += 1
            api_key_obj.last_used_at = datetime.datetime.now(datetime.timezone.utc)
            session.add(api_key_obj)
            await session.flush()
        return await session.get(User, api_key_obj.user_id)

    if len(matches) > 1:
        key_ids = [str(m.id) for m in matches]
        logger.error(
            "Data integrity violation: %d API keys share hash %s (key IDs: %s). Refusing to authenticate.",
            len(matches),
            incoming_hash[:12] + "...",
            ", ".join(key_ids),
        )
        return None

    # Slow path: legacy keys without hash (plaintext from 1.6.x or encrypted without hash)
    query = select(ApiKey).where(ApiKey.api_key_hash.is_(None))  # type: ignore[union-attr]
    legacy_keys = (await session.exec(query)).all()

    for api_key_obj in legacy_keys:
        stored_value = api_key_obj.api_key
        if stored_value is None:
            continue

        # decrypt_api_key returns "" on failure (never raises for decryption errors)
        if stored_value == api_key:
            matched = True
        else:
            candidate = auth_utils.decrypt_api_key(stored_value)
            matched = candidate == api_key

        if matched:
            # Backfill hash for future O(1) lookups
            api_key_obj.api_key_hash = incoming_hash
            if settings_service.settings.disable_track_apikey_usage is not True:
                api_key_obj.total_uses += 1
                api_key_obj.last_used_at = datetime.datetime.now(datetime.timezone.utc)
            session.add(api_key_obj)
            await session.flush()
            return await session.get(User, api_key_obj.user_id)

    return None