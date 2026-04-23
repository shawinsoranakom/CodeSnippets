def migrate(
    config_dir: Path,
    database_url: str,
    old_key: str | None = None,
    new_key: str | None = None,
    *,
    dry_run: bool = False,
):
    """Run the secret key migration.

    Args:
        config_dir: Path to Langflow config directory containing secret_key file.
        database_url: SQLAlchemy database connection URL.
        old_key: Current secret key. If None, reads from config_dir/secret_key.
        new_key: New secret key. If None, generates a secure random key.
        dry_run: If True, simulates migration without making changes.

    The migration runs as an atomic transaction - either all database changes
    succeed or none are applied. Key files are only modified after successful
    database migration.
    """
    # Determine old key
    if not old_key:
        old_key = read_secret_key_from_file(config_dir)
    if not old_key:
        print("Error: Could not find current secret key.")
        print(f"  Checked: {config_dir}/secret_key")
        print("  Use --old-key to provide it explicitly")
        sys.exit(1)

    # Determine new key
    if not new_key:
        new_key = secrets.token_urlsafe(32)
        print(f"Generated new secret key: {new_key}")
    else:
        print(f"Using provided new key: {new_key}")
    print("  (Save this key - you'll need it if the migration fails after database commit)")

    if old_key == new_key:
        print("Error: Old and new secret keys are the same")
        sys.exit(1)

    print("\nConfiguration:")
    print(f"  Config dir: {config_dir}")
    db_display = (
        f"{database_url[:DATABASE_URL_DISPLAY_LENGTH]}..."
        if len(database_url) > DATABASE_URL_DISPLAY_LENGTH
        else database_url
    )
    print(f"  Database: {db_display}")
    print(f"  Dry run: {dry_run}")

    if dry_run:
        print("\n[DRY RUN] No changes will be made.\n")

    engine = create_engine(database_url)
    total_migrated = 0
    total_failed = 0

    # Use begin() for atomic transaction - all changes commit together or rollback on failure
    with engine.begin() as conn:
        # Migrate user.store_api_key
        print("\n1. Migrating user.store_api_key...")
        users = conn.execute(text('SELECT id, store_api_key FROM "user" WHERE store_api_key IS NOT NULL')).fetchall()

        migrated, failed = 0, 0
        for user_id, encrypted_key in users:
            new_encrypted = migrate_value(encrypted_key, old_key, new_key)
            if new_encrypted:
                if not dry_run:
                    conn.execute(
                        text('UPDATE "user" SET store_api_key = :val WHERE id = :id'),
                        {"val": new_encrypted, "id": user_id},
                    )
                migrated += 1
            else:
                failed += 1
                print(f"   Warning: Could not decrypt for user {user_id}")

        print(f"   {'Would migrate' if dry_run else 'Migrated'}: {migrated}, Failed: {failed}")
        total_migrated += migrated
        total_failed += failed

        # Migrate variable.value (only Credential type variables are encrypted)
        print("\n2. Migrating credential variable values...")
        variables = conn.execute(
            text("SELECT id, name, value FROM variable WHERE type = :type"),
            {"type": CREDENTIAL_TYPE},
        ).fetchall()

        migrated, failed, skipped = 0, 0, 0
        for var_id, var_name, encrypted_value in variables:
            if not encrypted_value:
                skipped += 1
                continue
            new_encrypted = migrate_value(encrypted_value, old_key, new_key)
            if new_encrypted:
                if not dry_run:
                    conn.execute(
                        text("UPDATE variable SET value = :val WHERE id = :id"),
                        {"val": new_encrypted, "id": var_id},
                    )
                migrated += 1
            else:
                failed += 1
                print(f"   Warning: Could not decrypt variable '{var_name}' ({var_id})")

        print(f"   {'Would migrate' if dry_run else 'Migrated'}: {migrated}, Failed: {failed}, Skipped: {skipped}")
        total_migrated += migrated
        total_failed += failed

        # Migrate folder.auth_settings
        print("\n3. Migrating folder.auth_settings (MCP)...")
        folders = conn.execute(
            text("SELECT id, name, auth_settings FROM folder WHERE auth_settings IS NOT NULL")
        ).fetchall()

        migrated, failed = 0, 0
        for folder_id, folder_name, auth_settings in folders:
            if not auth_settings:
                continue
            try:
                settings_dict = auth_settings if isinstance(auth_settings, dict) else json.loads(auth_settings)
                new_settings, failed_fields = migrate_auth_settings(settings_dict, old_key, new_key)
                if failed_fields:
                    failed += 1
                    print(f"   Warning: Could not migrate folder '{folder_name}' fields: {', '.join(failed_fields)}")
                    continue
                if not dry_run:
                    conn.execute(
                        text("UPDATE folder SET auth_settings = :val WHERE id = :id"),
                        {"val": json.dumps(new_settings), "id": folder_id},
                    )
                migrated += 1
            except (json.JSONDecodeError, InvalidToken, TypeError, KeyError) as e:
                failed += 1
                print(f"   Warning: Could not migrate folder '{folder_name}': {e}")

        print(f"   {'Would migrate' if dry_run else 'Migrated'}: {migrated}, Failed: {failed}")
        total_migrated += migrated
        total_failed += failed

        # Verify migrated data can be decrypted with new key
        if total_migrated > 0:
            print("\n4. Verifying migration...")
            verified, verify_failed = verify_migration(conn, new_key)
            if verify_failed > 0:
                print(f"   ERROR: {verify_failed} records failed verification!")
                print("   Rolling back transaction...")
                conn.rollback()
                sys.exit(1)
            if verified > 0:
                print(f"   Verified {verified} sample records can be decrypted with new key")
            else:
                print("   No records to verify (all tables empty)")

        # Rollback if dry run (transaction will auto-commit on exit otherwise)
        if dry_run:
            conn.rollback()

    # Save new key only after successful database migration
    if not dry_run:
        backup_file = config_dir / f"secret_key.backup.{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        write_secret_key_to_file(config_dir, old_key, backup_file.name)
        print(f"\n5. Backed up old key to: {backup_file}")
        write_secret_key_to_file(config_dir, new_key)
        print(f"6. Saved new secret key to: {config_dir / 'secret_key'}")
    else:
        print("\n5. [DRY RUN] Would backup old key")
        print(f"6. [DRY RUN] Would save new key to: {config_dir / 'secret_key'}")

    # Summary
    print("\n" + "=" * 50)
    if dry_run:
        print("DRY RUN COMPLETE")
        print(f"\nWould migrate {total_migrated} items, {total_failed} failures")
        print("\nRun without --dry-run to apply changes.")
    else:
        print("MIGRATION COMPLETE")
        print(f"\nMigrated {total_migrated} items, {total_failed} failures")
        print(f"\nBackup key location: {config_dir}/secret_key.backup.*")
        print("\nNext steps:")
        print("1. Start Langflow and verify everything works")
        print("2. Users must log in again (JWT sessions invalidated)")
        print("3. Once verified, you may delete the backup key file")

    if total_failed > 0:
        print(f"\nWarning: {total_failed} items could not be migrated.")
        print("These may have been encrypted with a different key or are corrupted.")
        sys.exit(1 if not dry_run else 0)