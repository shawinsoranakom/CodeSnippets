def find_matching_credential(
    available_creds: list[Credentials],
    field_info: CredentialsFieldInfo,
) -> Credentials | None:
    """Find a credential that matches the required provider, type, scopes, and host."""
    for cred in available_creds:
        if cred.provider not in field_info.provider:
            continue
        if cred.type not in field_info.supported_types:
            continue
        if cred.type == "oauth2" and not _credential_has_required_scopes(
            cred, field_info
        ):
            continue
        if cred.type == "host_scoped" and not _credential_is_for_host(cred, field_info):
            continue
        return cred
    return None