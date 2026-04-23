async def save_app_conversation_info(
        self, info: AppConversationInfo
    ) -> AppConversationInfo:
        """Save conversation info and create/update SAAS metadata with user_id and org_id."""
        # Save the base conversation metadata
        await super().save_app_conversation_info(info)

        # Get current user_id for SAAS metadata
        # Fall back to info.created_by_user_id for webhook callbacks (which use ADMIN context)
        user_id_str = await self.user_context.get_user_id()
        if not user_id_str and info.created_by_user_id:
            user_id_str = info.created_by_user_id
        if user_id_str:
            # Convert string user_id to UUID
            user_id_uuid = UUID(user_id_str)
            user_query = select(User).where(User.id == user_id_uuid)
            user_result = await self.db_session.execute(user_query)
            user = user_result.scalar_one_or_none()
            assert user

            # Determine org_id: prefer API key's org_id if authenticated via API key
            org_id = user.current_org_id  # Default fallback
            if hasattr(self.user_context, 'user_auth'):
                user_auth = self.user_context.user_auth
                if hasattr(user_auth, 'get_api_key_org_id'):
                    api_key_org_id = user_auth.get_api_key_org_id()
                    if api_key_org_id is not None:
                        org_id = api_key_org_id

            # Override with resolver org_id if set (from git org claim resolution)
            resolver_org_id = getattr(self.user_context, 'resolver_org_id', None)
            if resolver_org_id is not None:
                org_id = resolver_org_id

            # Check if SAAS metadata already exists
            saas_query = select(StoredConversationMetadataSaas).where(
                StoredConversationMetadataSaas.conversation_id == str(info.id)
            )
            saas_result = await self.db_session.execute(saas_query)
            existing_saas_metadata = saas_result.scalar_one_or_none()
            assert existing_saas_metadata is None or (
                existing_saas_metadata.user_id == user_id_uuid
                and existing_saas_metadata.org_id == org_id
            )

            if not existing_saas_metadata:
                # Create new SAAS metadata with the determined org_id
                saas_metadata = StoredConversationMetadataSaas(
                    conversation_id=str(info.id),
                    user_id=user_id_uuid,
                    org_id=org_id,
                )
                self.db_session.add(saas_metadata)

            await self.db_session.commit()

        return info