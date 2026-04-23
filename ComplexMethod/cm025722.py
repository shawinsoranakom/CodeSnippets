def _validate_credential_data(
    lock_endpoint: MatterEndpoint, credential_type: str, credential_data: str
) -> None:
    """Validate credential data against lock constraints.

    For PIN: checks digits-only and length against Min/MaxPINCodeLength.
    For RFID: checks valid hex and byte length against Min/MaxRFIDCodeLength.
    Raises CredentialDataInvalidError on failure.
    """
    if credential_type == CRED_TYPE_PIN:
        if not credential_data.isdigit():
            raise CredentialDataInvalidError(
                translation_domain="matter",
                translation_key=ERR_INVALID_CREDENTIAL_DATA,
                translation_placeholders={"reason": "PIN must contain only digits"},
            )
        min_len = (
            lock_endpoint.get_attribute_value(
                None, clusters.DoorLock.Attributes.MinPINCodeLength
            )
            or 0
        )
        max_len = (
            lock_endpoint.get_attribute_value(
                None, clusters.DoorLock.Attributes.MaxPINCodeLength
            )
            or 255
        )
        if not min_len <= len(credential_data) <= max_len:
            raise CredentialDataInvalidError(
                translation_domain="matter",
                translation_key=ERR_INVALID_CREDENTIAL_DATA,
                translation_placeholders={
                    "reason": (f"PIN length must be between {min_len} and {max_len}")
                },
            )

    elif credential_type == CRED_TYPE_RFID:
        try:
            rfid_bytes = bytes.fromhex(credential_data)
        except ValueError as err:
            raise CredentialDataInvalidError(
                translation_domain="matter",
                translation_key=ERR_INVALID_CREDENTIAL_DATA,
                translation_placeholders={
                    "reason": "RFID data must be valid hexadecimal"
                },
            ) from err
        min_len = (
            lock_endpoint.get_attribute_value(
                None, clusters.DoorLock.Attributes.MinRFIDCodeLength
            )
            or 0
        )
        max_len = (
            lock_endpoint.get_attribute_value(
                None, clusters.DoorLock.Attributes.MaxRFIDCodeLength
            )
            or 255
        )
        if not min_len <= len(rfid_bytes) <= max_len:
            raise CredentialDataInvalidError(
                translation_domain="matter",
                translation_key=ERR_INVALID_CREDENTIAL_DATA,
                translation_placeholders={
                    "reason": (
                        f"RFID data length must be between"
                        f" {min_len} and {max_len} bytes"
                    )
                },
            )