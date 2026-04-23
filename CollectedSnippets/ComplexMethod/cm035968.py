async def load(self) -> Settings | None:
        user = await UserStore.get_user_by_id(self.user_id)
        if not user:
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
        org = await OrgStore.get_org_by_id_async(org_id)
        if not org:
            logger.error(
                f'Org not found for ID {org_id} as the current org for user {self.user_id}'
            )
            return None
        org_agent_settings = OrgStore.get_agent_settings_from_org(org)
        member_agent_settings_diff = dict(org_member.agent_settings_diff)

        kwargs = {
            **{
                normalized: getattr(org, c.name)
                for c in Org.__table__.columns
                if (
                    normalized := c.name.removeprefix('_default_')
                    .removeprefix('default_')
                    .lstrip('_')
                )
                in Settings.model_fields
            },
            **{
                normalized: getattr(user, c.name)
                for c in User.__table__.columns
                if (normalized := c.name.lstrip('_')) in Settings.model_fields
            },
        }
        merged_agent_settings = deep_merge(
            org_agent_settings.model_dump(mode='json'),
            member_agent_settings_diff,
        )
        effective_llm_api_key = self._get_effective_llm_api_key(org, org_member)
        if effective_llm_api_key is not None:
            merged_agent_settings.setdefault('llm', {})['api_key'] = (
                effective_llm_api_key.get_secret_value()
                if isinstance(effective_llm_api_key, SecretStr)
                else effective_llm_api_key
            )
        else:
            logger.warning(
                f'No effective LLM API key found for user {self.user_id} '
                f'in org {org_id} (org key and member key are both unset)'
            )
        kwargs['agent_settings'] = merged_agent_settings
        org_conversation = OrgStore.get_conversation_settings_from_org(org)
        member_conversation_diff = dict(org_member.conversation_settings_diff)
        kwargs['conversation_settings'] = deep_merge(
            org_conversation.model_dump(mode='json'),
            member_conversation_diff,
        )
        if org.v1_enabled is None:
            kwargs['v1_enabled'] = True
        # Apply default if sandbox_grouping_strategy is None in the database
        if kwargs.get('sandbox_grouping_strategy') is None:
            kwargs.pop('sandbox_grouping_strategy', None)

        return Settings(**kwargs)