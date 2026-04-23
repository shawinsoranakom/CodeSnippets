def get_account_id_from_access_key_id(access_key_id: str) -> str:
    """Return the Account ID associated the Access Key ID."""

    # If AWS_ACCESS_KEY_ID has a 12-digit integer value, use it as the account ID
    if re.match(r"\d{12}", access_key_id):
        return access_key_id

    elif len(access_key_id) >= 20:
        if not config.PARITY_AWS_ACCESS_KEY_ID:
            # If AWS_ACCESS_KEY_ID has production AWS credentials, ignore them
            if access_key_id.startswith("ASIA") or access_key_id.startswith("AKIA"):
                LOG.debug(
                    "Ignoring production AWS credentials provided to LocalStack. Falling back to default account ID."
                )

            elif access_key_id.startswith("LSIA") or access_key_id.startswith("LKIA"):
                return extract_account_id_from_access_key_id(access_key_id)
        else:
            if access_key_id.startswith("ASIA") or access_key_id.startswith("AKIA"):
                return extract_account_id_from_access_key_id(access_key_id)

    return DEFAULT_AWS_ACCOUNT_ID