async def store(self, item: Settings):
        async with a_session_maker() as session:
            if not item:
                return None
            result = await session.execute(
                select(User)
                .options(joinedload(User.org_members))
                .filter(User.id == uuid.UUID(self.user_id))
            )
            user = result.scalars().first()

            if not user:
                # Check if we need to migrate from user_settings
                user_settings = None
                async with a_session_maker() as new_session:
                    user_settings = await self._get_user_settings_by_keycloak_id_async(
                        self.user_id, new_session
                    )
                if user_settings:
                    token_manager = TokenManager()
                    user_info = await token_manager.get_user_info_from_user_id(
                        self.user_id
                    )
                    if not user_info:
                        logger.error(f'User info not found for ID {self.user_id}')
                        return None
                    user = await UserStore.migrate_user(
                        self.user_id, user_settings, user_info
                    )
                    if not user:
                        logger.error(f'Failed to migrate user {self.user_id}')
                        return None
                else:
                    logger.error(f'User not found for ID {self.user_id}')
                    return None

            org_id = user.current_org_id

            org_member: OrgMember | None = None
            for om in user.org_members:
                if om.org_id == org_id:
                    org_member = om
                    break
            if not org_member:
                return None

            result = await session.execute(select(Org).filter(Org.id == org_id))
            org = result.scalars().first()
            if not org:
                logger.error(
                    f'Org not found for ID {org_id} as the current org for user {self.user_id}'
                )
                return None

            llm_model = item.agent_settings.llm.model
            llm_base_url = item.agent_settings.llm.base_url
            normalized_llm_base_url = llm_base_url.rstrip('/') if llm_base_url else None
            normalized_managed_base_url = LITE_LLM_API_URL.rstrip('/')
            uses_managed_llm_key = (
                normalized_llm_base_url == normalized_managed_base_url
                or (normalized_llm_base_url is None and is_openhands_model(llm_model))
            )

            if uses_managed_llm_key:
                await self._ensure_api_key(
                    item, str(org_id), openhands_type=is_openhands_model(llm_model)
                )

            effective_agent_settings_diff = self._get_persisted_agent_settings(item)
            org.agent_settings = deep_merge(
                OrgStore.get_agent_settings_from_org(org).model_dump(mode='json'),
                effective_agent_settings_diff,
            )

            effective_conversation_diff = item.conversation_settings.model_dump(
                mode='json'
            )
            org.conversation_settings = deep_merge(
                OrgStore.get_conversation_settings_from_org(org).model_dump(
                    mode='json'
                ),
                effective_conversation_diff,
            )

            kwargs = item.model_dump(context={'expose_secrets': True})
            kwargs.pop('agent_settings', None)
            kwargs.pop('conversation_settings', None)

            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
                if hasattr(org, key) and key not in {
                    'llm_api_key',
                    'agent_settings',
                    'conversation_settings',
                }:
                    setattr(org, key, value)

            current_member_llm_api_key = item.agent_settings.llm.api_key
            org_default_llm_api_key = org.llm_api_key
            org_default_llm_api_key_raw = (
                org_default_llm_api_key.get_secret_value()
                if org_default_llm_api_key
                else None
            )
            current_member_llm_api_key_raw = (
                current_member_llm_api_key.get_secret_value()
                if current_member_llm_api_key
                else None
            )

            await OrgMemberStore.update_all_members_settings_async(
                session,
                org_id,
                OrgMemberSettingsUpdate(
                    agent_settings_diff=effective_agent_settings_diff,
                    conversation_settings_diff=effective_conversation_diff,
                    llm_api_key=(
                        current_member_llm_api_key_raw
                        if not uses_managed_llm_key
                        else None
                    ),
                ),
            )

            if uses_managed_llm_key and current_member_llm_api_key is not None:
                # Managed/proxy key — store on this member but mark as org-managed
                org_member.llm_api_key = current_member_llm_api_key
                org_member.has_custom_llm_api_key = False
            elif current_member_llm_api_key_raw is not None:
                # BYOR: member supplied their own (non-managed) API key
                org_member.llm_api_key = current_member_llm_api_key
                org_member.has_custom_llm_api_key = True
            elif org_default_llm_api_key_raw is not None:
                # No member key, falling back to org default
                org_member.has_custom_llm_api_key = False

            await session.commit()