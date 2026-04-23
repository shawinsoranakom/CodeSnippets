async def _verify_existing_key(
        client: httpx.AsyncClient,
        key_value: str,
        keycloak_user_id: str,
        org_id: str,
        openhands_type: bool = False,
    ) -> bool:
        """Check if an existing key exists for the user/org in LiteLLM.

        Verifies the provided key_value matches a key registered in LiteLLM for
        the given user and organization. For openhands_type=True, looks for keys
        with metadata type='openhands' and matching team_id. For openhands_type=False,
        looks for keys with matching alias and team_id.

        Returns True if the key is found and valid, False otherwise.
        """
        found = False
        keys = await LiteLlmManager._get_all_keys_for_user(client, keycloak_user_id)
        for key_info in keys:
            metadata = key_info.get('metadata') or {}
            team_id = key_info.get('team_id')
            key_alias = key_info.get('key_alias')
            token = None
            if (
                openhands_type
                and metadata.get('type') == 'openhands'
                and team_id == org_id
            ):
                # Found an existing OpenHands key for this org
                key_name = key_info.get('key_name')
                token = key_name[-4:] if key_name else None  # last 4 digits of key
                if token and key_value.endswith(
                    token
                ):  # check if this is our current key
                    found = True
                    break
            if (
                not openhands_type
                and team_id == org_id
                and (
                    key_alias == get_openhands_cloud_key_alias(keycloak_user_id, org_id)
                    or key_alias == get_byor_key_alias(keycloak_user_id, org_id)
                )
            ):
                # Found an existing key for this org (regardless of type)
                key_name = key_info.get('key_name')
                token = key_name[-4:] if key_name else None  # last 4 digits of key
                if token and key_value.endswith(
                    token
                ):  # check if this is our current key
                    found = True
                    break

        return found