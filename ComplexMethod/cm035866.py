async def _validate_conversation_ownership(self, conversation_id: str) -> None:
        """Validate that the current user owns the conversation.

        This ensures multi-tenant isolation by checking:
        - The conversation belongs to the current user
        - The conversation belongs to the user's current organization

        Args:
            conversation_id: The conversation ID to validate (can be task-id or UUID)

        Raises:
            AuthError: If user doesn't own the conversation or authentication fails
        """
        # For internal operations (e.g., processing pending messages during startup)
        # we need a mode that bypasses filtering. The ADMIN context enables this.
        if self.user_context == ADMIN:
            return

        user_id_str = await self.user_context.get_user_id()
        if not user_id_str:
            raise AuthError('User authentication required')

        user_id_uuid = UUID(user_id_str)

        # Check conversation ownership via SAAS metadata
        query = select(StoredConversationMetadataSaas).where(
            StoredConversationMetadataSaas.conversation_id == conversation_id
        )
        result = await self.db_session.execute(query)
        saas_metadata = result.scalar_one_or_none()

        # If no SAAS metadata exists, the conversation might be a new task-id
        # that hasn't been linked to a conversation yet. Allow access in this case
        # as the message will be validated when the conversation is created.
        if saas_metadata is None:
            return

        # Verify user ownership
        if saas_metadata.user_id != user_id_uuid:
            raise AuthError('You do not have access to this conversation')

        # Verify organization ownership if applicable
        user = await self._get_current_user()
        if user and user.current_org_id is not None:
            if saas_metadata.org_id != user.current_org_id:
                raise AuthError('Conversation belongs to a different organization')