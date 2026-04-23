def do_unvault(vault, secret, vault_id='filter_default'):
    if isinstance(vault, VaultExceptionMarker):
        vault = vault._disarm()

    if (first_marker := _template.get_first_marker_arg((vault, secret, vault_id), {})) is not None:
        return first_marker

    if not isinstance(secret, (str, bytes)):
        raise TypeError(f"Secret passed is required to be as string, instead we got {type(secret)}.")

    if not isinstance(vault, (str, bytes)):
        raise TypeError(f"Vault should be in the form of a string, instead we got {type(vault)}.")

    vs = VaultSecret(to_bytes(secret))
    vl = VaultLib([(vault_id, vs)])

    if ciphertext := VaultHelper.get_ciphertext(vault, with_tags=True):
        vault = ciphertext

    if is_encrypted(vault):
        try:
            data = vl.decrypt(vault)
        except Exception as ex:
            raise AnsibleError("Unable to decrypt.") from ex
    else:
        data = vault

    return to_native(data)