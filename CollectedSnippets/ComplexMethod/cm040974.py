def _get_kms_key(
        account_id: str,
        region_name: str,
        any_type_of_key_id: str,
        any_key_state_allowed: bool = False,
        enabled_key_allowed: bool = True,
        disabled_key_allowed: bool = False,
        pending_deletion_key_allowed: bool = False,
    ) -> KmsKey:
        store = kms_stores[account_id][region_name]

        if any_key_state_allowed:
            enabled_key_allowed = True
            disabled_key_allowed = True
            pending_deletion_key_allowed = True
        if not (enabled_key_allowed or disabled_key_allowed or pending_deletion_key_allowed):
            raise ValueError("A key is requested, but all possible key states are prohibited")

        key_id = KmsProvider._get_key_id_from_any_id(account_id, region_name, any_type_of_key_id)
        key = store.keys[key_id]

        if not disabled_key_allowed and key.metadata.get("KeyState") == "Disabled":
            raise DisabledException(f"{key.metadata.get('Arn')} is disabled.")
        if not pending_deletion_key_allowed and key.metadata.get("KeyState") == "PendingDeletion":
            raise KMSInvalidStateException(f"{key.metadata.get('Arn')} is pending deletion.")
        if not enabled_key_allowed and key.metadata.get("KeyState") == "Enabled":
            raise KMSInvalidStateException(
                f"{key.metadata.get('Arn')} is enabled, but the operation doesn't support "
                f"such a state"
            )
        return store.keys[key_id]