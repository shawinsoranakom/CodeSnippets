async def _maybe_get_managed_llm_key_for_user(
        session,
        updated_org: Org,
        user_id: str,
    ) -> str | None:
        """Return the managed LLM key every member row should carry, if any."""
        llm_settings = OrgStore.get_agent_settings_from_org(updated_org).llm
        llm_model = llm_settings.model
        llm_base_url = llm_settings.base_url
        normalized_llm_base_url = llm_base_url.rstrip('/') if llm_base_url else None
        normalized_managed_base_url = LITE_LLM_API_URL.rstrip('/')
        openhands_type = is_openhands_model(llm_model)
        uses_managed_llm_key = (
            normalized_llm_base_url == normalized_managed_base_url
            or (normalized_llm_base_url is None and openhands_type)
        )
        if not uses_managed_llm_key:
            return None

        result = await session.execute(
            select(OrgMember).where(
                OrgMember.org_id == updated_org.id,
                OrgMember.user_id == UUID(user_id),
            )
        )
        acting_member = result.scalars().first()
        if acting_member is None:
            logger.error(
                'Acting member row not found during managed LLM key '
                'rotation; skipping managed-key propagation. Members may '
                'retain stale keys until they save personal settings.',
                extra={'user_id': user_id, 'org_id': str(updated_org.id)},
            )
            return None

        existing_key = acting_member.llm_api_key
        existing_key_raw = existing_key.get_secret_value() if existing_key else None
        if existing_key_raw and await LiteLlmManager.verify_existing_key(
            existing_key_raw,
            user_id,
            str(updated_org.id),
            openhands_type=openhands_type,
        ):
            return existing_key_raw

        if openhands_type:
            logger.info(
                'Generated managed LLM key for acting user on org-defaults save',
                extra={'user_id': user_id, 'org_id': str(updated_org.id)},
            )
            return await LiteLlmManager.generate_key(
                user_id,
                str(updated_org.id),
                None,
                {'type': 'openhands'},
            )

        key_alias = get_openhands_cloud_key_alias(user_id, str(updated_org.id))
        await LiteLlmManager.delete_key_by_alias(key_alias=key_alias)
        logger.info(
            'Generated managed LLM key for acting user on org-defaults save',
            extra={'user_id': user_id, 'org_id': str(updated_org.id)},
        )
        return await LiteLlmManager.generate_key(
            user_id,
            str(updated_org.id),
            key_alias,
            None,
        )