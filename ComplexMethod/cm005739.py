def verify_migration(conn, new_key: str) -> tuple[int, int]:
    """Verify migrated data can be decrypted with the new key.

    Samples records from each table and attempts decryption.

    Returns:
        Tuple of (verified_count, failed_count).
    """
    verified, failed = 0, 0

    # Verify user.store_api_key (sample up to 3)
    users = conn.execute(
        text('SELECT id, store_api_key FROM "user" WHERE store_api_key IS NOT NULL LIMIT 3')
    ).fetchall()
    for _, encrypted_key in users:
        try:
            decrypt_with_key(encrypted_key, new_key)
            verified += 1
        except InvalidToken:
            failed += 1

    # Verify variable.value (sample up to 3)
    variables = conn.execute(
        text("SELECT id, value FROM variable WHERE type = :type AND value IS NOT NULL LIMIT 3"),
        {"type": CREDENTIAL_TYPE},
    ).fetchall()
    for _, encrypted_value in variables:
        try:
            decrypt_with_key(encrypted_value, new_key)
            verified += 1
        except InvalidToken:
            failed += 1

    # Verify folder.auth_settings (sample up to 3)
    folders = conn.execute(
        text("SELECT id, auth_settings FROM folder WHERE auth_settings IS NOT NULL LIMIT 3")
    ).fetchall()
    for _, auth_settings in folders:
        if not auth_settings:
            continue
        try:
            settings_dict = auth_settings if isinstance(auth_settings, dict) else json.loads(auth_settings)
            for field in SENSITIVE_AUTH_FIELDS:
                if settings_dict.get(field):
                    decrypt_with_key(settings_dict[field], new_key)
                    verified += 1
        except (InvalidToken, json.JSONDecodeError):
            failed += 1

    return verified, failed