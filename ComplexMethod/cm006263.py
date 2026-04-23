def downgrade() -> None:
    """Decrypt sensitive fields in auth_settings data (for rollback)."""
    conn = op.get_bind()

    # Import decryption utilities
    try:
        from langflow.services.auth.mcp_encryption import decrypt_auth_settings
        from langflow.services.deps import get_settings_service

        # Check if the folder table exists
        inspector = sa.inspect(conn)
        if 'folder' not in inspector.get_table_names():
            return

        # Query all folders with auth_settings
        result = conn.execute(
            sa.text("SELECT id, auth_settings FROM folder WHERE auth_settings IS NOT NULL")
        )

        # Decrypt auth_settings for each folder
        for row in result:
            folder_id = row.id
            auth_settings = row.auth_settings

            if auth_settings:
                try:
                    # Parse JSON if it's a string
                    if isinstance(auth_settings, str):
                        auth_settings_dict = json.loads(auth_settings)
                    else:
                        auth_settings_dict = auth_settings

                    # Decrypt sensitive fields
                    decrypted_settings = decrypt_auth_settings(auth_settings_dict)

                    # Update the record with decrypted data
                    if decrypted_settings:
                        conn.execute(
                            sa.text("UPDATE folder SET auth_settings = :auth_settings WHERE id = :id"),
                            {"auth_settings": json.dumps(decrypted_settings), "id": folder_id}
                        )
                except Exception as e:
                    # Log the error but continue with other records
                    print(f"Warning: Failed to decrypt auth_settings for folder {folder_id}: {e}")

    except ImportError as e:
        # If decryption utilities are not available, skip the migration
        print(f"Warning: Decryption utilities not available, skipping decryption migration: {e}")