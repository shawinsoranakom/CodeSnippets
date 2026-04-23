async def _update_org_kwargs(
        org_id: UUID,
        org_kwargs: dict[str, Any],
        user_id: str | None = None,
        update_data: OrgUpdate | None = None,
    ) -> Optional[Org]:
        """Internal helper for updating organization fields from raw kwargs."""
        from storage.org_member_store import OrgMemberStore

        org_kwargs = dict(org_kwargs)

        async with a_session_maker() as session:
            result = await session.execute(select(Org).filter(Org.id == org_id))
            org = result.scalars().first()
            if not org:
                return None

            if 'id' in org_kwargs:
                org_kwargs.pop('id')

            # Pop the diff-style kwargs before the setattr loop — otherwise
            # ``hasattr(org, 'agent_settings')`` is True and the loop would
            # *overwrite* the JSON column instead of deep-merging into it.
            agent_settings_diff = (
                update_data.agent_settings_diff
                if update_data is not None
                else org_kwargs.pop('agent_settings_diff', None)
            )
            conversation_settings_diff = (
                update_data.conversation_settings_diff
                if update_data is not None
                else org_kwargs.pop('conversation_settings_diff', None)
            )
            for key, value in org_kwargs.items():
                if hasattr(org, key):
                    setattr(org, key, value)

            if agent_settings_diff is not None:
                org.agent_settings = OrgStore._merge_and_validate_settings(
                    org.agent_settings,
                    agent_settings_diff,
                    AgentSettings,
                ).model_dump(mode='json', exclude_unset=True)

            if conversation_settings_diff is not None:
                org.conversation_settings = OrgStore._merge_and_validate_settings(
                    org.conversation_settings,
                    conversation_settings_diff,
                    ConversationSettings,
                ).model_dump(mode='json', exclude_unset=True)

            if update_data is not None and update_data.touches_org_defaults():
                if user_id is None:
                    raise ValueError(
                        'user_id is required when updating organization defaults'
                    )

                member_updates = update_data.get_member_updates()
                effective_managed_key = (
                    await OrgStore._maybe_get_managed_llm_key_for_user(
                        session,
                        org,
                        user_id,
                    )
                )
                should_reset_custom_key_flag = (
                    update_data.llm_api_key is not None
                    or effective_managed_key is not None
                )
                if effective_managed_key is not None:
                    if member_updates is None:
                        member_updates = OrgMemberSettingsUpdate()
                    member_updates.llm_api_key = SecretStr(effective_managed_key)

                if member_updates is not None:
                    if should_reset_custom_key_flag:
                        member_updates.has_custom_llm_api_key = False
                    await OrgMemberStore.update_all_members_settings_async(
                        session, org_id, member_updates
                    )

            await session.commit()
            await session.refresh(org)
            return org