def decrypt_auth_settings(auth_settings: dict[str, Any] | None) -> dict[str, Any] | None:
    """Decrypt sensitive fields in auth_settings dictionary.

    Args:
        auth_settings: Dictionary containing encrypted authentication settings

    Returns:
        Dictionary with sensitive fields decrypted, or None if input is None
    """
    if auth_settings is None:
        return None

    decrypted_settings = auth_settings.copy()

    for field in SENSITIVE_FIELDS:
        if decrypted_settings.get(field):
            try:
                field_to_decrypt = decrypted_settings[field]

                decrypted_value = auth_utils.decrypt_api_key(field_to_decrypt)
                if not decrypted_value:
                    msg = f"Failed to decrypt field {field}"
                    raise ValueError(msg)

                decrypted_settings[field] = decrypted_value
            except (ValueError, TypeError, KeyError, InvalidToken) as e:
                # If decryption fails, check if the value appears encrypted
                field_value = field_to_decrypt
                if isinstance(field_value, str) and field_value.startswith("gAAAAAB"):
                    # Value appears to be encrypted but decryption failed
                    logger.error(f"Failed to decrypt encrypted field {field}: {e}")
                    # For OAuth flows, we need the decrypted value, so raise the error
                    msg = f"Unable to decrypt {field}. Check encryption key configuration."
                    raise ValueError(msg) from e

                # Value doesn't appear encrypted, assume it's plaintext (backward compatibility)
                logger.debug(f"Field {field} appears to be plaintext, keeping original value")

    return decrypted_settings