async def accept_invitation(token: str, user_id: UUID) -> OrgInvitation:
        """Accept an organization invitation.

        This method:
        1. Validates the token and invitation status
        2. Checks expiration
        3. Verifies user is not already a member
        4. Creates LiteLLM integration
        5. Adds user to the organization
        6. Marks invitation as accepted

        Args:
            token: The invitation token
            user_id: The user accepting the invitation

        Returns:
            OrgInvitation: The accepted invitation

        Raises:
            InvitationInvalidError: If token is invalid or invitation not pending
            InvitationExpiredError: If invitation has expired
            UserAlreadyMemberError: If user is already a member
        """
        logger.info(
            'Accepting organization invitation',
            extra={
                'token_prefix': token[:10] + '...' if len(token) > 10 else token,
                'user_id': str(user_id),
            },
        )

        # Step 1: Get and validate invitation
        invitation = await OrgInvitationStore.get_invitation_by_token(token)

        if not invitation:
            raise InvitationInvalidError('Invalid invitation token')

        if invitation.status != OrgInvitation.STATUS_PENDING:
            if invitation.status == OrgInvitation.STATUS_ACCEPTED:
                raise InvitationInvalidError('Invitation has already been accepted')
            elif invitation.status == OrgInvitation.STATUS_REVOKED:
                raise InvitationInvalidError('Invitation has been revoked')
            else:
                raise InvitationInvalidError('Invitation is no longer valid')

        # Step 2: Check expiration
        if OrgInvitationStore.is_token_expired(invitation):
            await OrgInvitationStore.update_invitation_status(
                invitation.id, OrgInvitation.STATUS_EXPIRED
            )
            raise InvitationExpiredError('Invitation has expired')

        # Step 2.5: Verify user email matches invitation email
        user = await UserStore.get_user_by_id(str(user_id))
        if not user:
            raise InvitationInvalidError('User not found')

        user_email = user.email
        # Fallback: fetch email from Keycloak if not in database (for existing users)
        if not user_email:
            token_manager = TokenManager()
            user_info = await token_manager.get_user_info_from_user_id(str(user_id))
            user_email = user_info.get('email') if user_info else None

        if not user_email:
            raise EmailMismatchError('Your account does not have an email address')

        user_email = user_email.lower().strip()
        invitation_email = invitation.email.lower().strip()

        if user_email != invitation_email:
            logger.warning(
                'Email mismatch during invitation acceptance',
                extra={
                    'user_id': str(user_id),
                    'user_email': user_email,
                    'invitation_email': invitation_email,
                    'invitation_id': invitation.id,
                },
            )
            raise EmailMismatchError()

        # Step 3: Check if user is already a member
        existing_member = await OrgMemberStore.get_org_member(
            invitation.org_id, user_id
        )
        if existing_member:
            raise UserAlreadyMemberError(
                'You are already a member of this organization'
            )

        # Step 4: Create LiteLLM integration for the user in the new org
        try:
            settings = await OrgService.create_litellm_integration(
                invitation.org_id, str(user_id)
            )
        except Exception as e:
            logger.error(
                'Failed to create LiteLLM integration for invitation acceptance',
                extra={
                    'invitation_id': invitation.id,
                    'user_id': str(user_id),
                    'org_id': str(invitation.org_id),
                    'error': str(e),
                },
            )
            raise InvitationInvalidError(
                'Failed to set up organization access. Please try again.'
            )

        # Step 4.5: Ensure the organization still exists before adding membership
        org = await OrgStore.get_org_by_id(invitation.org_id)
        if not org:
            raise InvitationInvalidError('Organization not found')

        # Step 5: Add user to organization. New members start with no
        # personal agent-setting overrides so future org default changes
        # continue to flow through automatically.
        llm_api_key_secret = settings.agent_settings.llm.api_key
        llm_api_key = (
            llm_api_key_secret.get_secret_value() if llm_api_key_secret else ''
        )

        await OrgMemberStore.add_user_to_org(
            org_id=invitation.org_id,
            user_id=user_id,
            role_id=invitation.role_id,
            llm_api_key=llm_api_key,
            status='active',
            agent_settings_diff={},
            conversation_settings_diff={},
        )

        # Step 6: Mark invitation as accepted
        updated_invitation = await OrgInvitationStore.update_invitation_status(
            invitation.id,
            OrgInvitation.STATUS_ACCEPTED,
            accepted_by_user_id=user_id,
        )

        if not updated_invitation:
            raise InvitationInvalidError('Failed to update invitation status')

        logger.info(
            'Organization invitation accepted',
            extra={
                'invitation_id': invitation.id,
                'user_id': str(user_id),
                'org_id': str(invitation.org_id),
                'role_id': invitation.role_id,
            },
        )

        return updated_invitation