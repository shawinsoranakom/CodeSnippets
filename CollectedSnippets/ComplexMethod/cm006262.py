def upgrade() -> None:
    """Encrypt sensitive fields in existing auth_settings data."""
    conn = op.get_bind()

    # Import encryption utilities
    try:
        from langflow.services.auth.mcp_encryption import encrypt_auth_settings
        from langflow.services.deps import get_settings_service

        # Check if the folder table exists
        inspector = sa.inspect(conn)
        if 'folder' not in inspector.get_table_names():
            return

        # Query all folders with auth_settings
        result = conn.execute(
            sa.text("SELECT id, auth_settings FROM folder WHERE auth_settings IS NOT NULL")
        )

        # Encrypt auth_settings for each folder
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

                    # Encrypt sensitive fields
                    encrypted_settings = encrypt_auth_settings(auth_settings_dict)

                    # Update the record with encrypted data
                    if encrypted_settings:
                        conn.execute(
                            sa.text("UPDATE folder SET auth_settings = :auth_settings WHERE id = :id"),
                            {"auth_settings": json.dumps(encrypted_settings), "id": folder_id}
                        )
                except Exception as e:
                    # Log the error but continue with other records
                    print(f"Warning: Failed to encrypt auth_settings for folder {folder_id}: {e}")

    except ImportError as e:
        # If encryption utilities are not available, skip the migration
        print(f"Warning: Encryption utilities not available, skipping encryption migration: {e}")