def _backfill_hashes(conn, decrypt_api_key) -> tuple[int, int, int, int]:
    """Backfill api_key_hash for rows where it is NULL.

    Decrypts each row, groups by plaintext, and only hashes unique-plaintext
    rows. Duplicate-plaintext groups are left with NULL hash so that the
    runtime fast-path lookup can never return multiple matches and fail
    closed. The runtime slow-path will match and backfill exactly one row
    per group on first use, leaving the remaining NULL rows as harmless
    orphans.

    Returns ``(backfilled, skipped, duplicate_groups, duplicate_rows)``.
    """
    rows = conn.execute(
        sa.text(f"SELECT id, api_key FROM {TABLE_NAME} WHERE api_key_hash IS NULL")  # noqa: S608
    ).fetchall()
    if not rows:
        return 0, 0, 0, 0

    # First pass: decrypt every row and group by plaintext.
    plaintext_to_ids: dict[str, list] = {}
    skipped = 0
    for row in rows:
        stored_key = row[1]
        if not stored_key:
            continue

        # Plaintext keys (1.6.x style) don't start with gAAAAA
        if not stored_key.startswith("gAAAAA"):
            plaintext = stored_key
        else:
            # decrypt_api_key returns "" on failure (never raises for decryption errors)
            try:
                plaintext = decrypt_api_key(stored_key)
            except Exception:  # noqa: BLE001
                skipped += 1
                continue
            if not plaintext:
                skipped += 1
                continue

        plaintext_to_ids.setdefault(plaintext, []).append(row[0])

    # Second pass: backfill only unique-plaintext rows.
    backfilled = 0
    duplicate_groups = 0
    duplicate_rows = 0
    for plaintext, ids in plaintext_to_ids.items():
        if len(ids) > 1:
            duplicate_groups += 1
            duplicate_rows += len(ids)
            continue
        conn.execute(
            sa.text(f"UPDATE {TABLE_NAME} SET api_key_hash = :hash WHERE id = :id"),  # noqa: S608
            {"hash": _hash_key(plaintext), "id": ids[0]},
        )
        backfilled += 1

    return backfilled, skipped, duplicate_groups, duplicate_rows