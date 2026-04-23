async def create_invitation(
        org_id: UUID,
        email: str,
        role_name: str,
        inviter_id: UUID,
    ) -> OrgInvitation:
        """Create a new organization invitation.

        This method:
        1. Validates the organization exists
        2. Validates this is not a personal workspace
        3. Checks inviter has owner/admin role
        4. Validates role assignment permissions
        5. Checks if user is already a member
        6. Creates the invitation
        7. Sends the invitation email

        Args:
            org_id: Organization UUID
            email: Invitee's email address
            role_name: Role to assign on acceptance (owner, admin, member)
            inviter_id: User ID of the person creating the invitation

        Returns:
            OrgInvitation: The created invitation

        Raises:
            ValueError: If organization or role not found
            InsufficientPermissionError: If inviter lacks permission
            UserAlreadyMemberError: If email is already a member
            InvitationAlreadyExistsError: If pending invitation exists
        """
        email = email.lower().strip()

        logger.info(
            'Creating organization invitation',
            extra={
                'org_id': str(org_id),
                'email': email,
                'role_name': role_name,
                'inviter_id': str(inviter_id),
            },
        )

        # Step 1: Validate organization exists
        org = await OrgStore.get_org_by_id(org_id)
        if not org:
            raise ValueError(f'Organization {org_id} not found')

        # Step 2: Check this is not a personal workspace
        # A personal workspace has org_id matching the user's id
        if str(org_id) == str(inviter_id):
            raise InsufficientPermissionError(
                'Cannot invite users to a personal workspace'
            )

        # Step 3: Check inviter is a member and has permission
        inviter_member = await OrgMemberStore.get_org_member(org_id, inviter_id)
        if not inviter_member:
            raise InsufficientPermissionError(
                'You are not a member of this organization'
            )

        inviter_role = await RoleStore.get_role_by_id(inviter_member.role_id)
        if not inviter_role or inviter_role.name not in [ROLE_OWNER, ROLE_ADMIN]:
            raise InsufficientPermissionError('Only owners and admins can invite users')

        # Step 4: Validate role assignment permissions
        role_name_lower = role_name.lower()
        if role_name_lower == ROLE_OWNER and inviter_role.name != ROLE_OWNER:
            raise InsufficientPermissionError('Only owners can invite with owner role')

        # Get the target role
        target_role = await RoleStore.get_role_by_name(role_name_lower)
        if not target_role:
            raise ValueError(f'Invalid role: {role_name}')

        # Step 5: Check if user is already a member (by email)
        existing_user = await UserStore.get_user_by_email(email)
        if existing_user:
            existing_member = await OrgMemberStore.get_org_member(
                org_id, existing_user.id
            )
            if existing_member:
                raise UserAlreadyMemberError(
                    'User is already a member of this organization'
                )

        # Step 6: Create the invitation
        invitation = await OrgInvitationStore.create_invitation(
            org_id=org_id,
            email=email,
            role_id=target_role.id,
            inviter_id=inviter_id,
        )

        # Step 7: Send invitation email
        try:
            # Get inviter info for the email
            inviter_user = await UserStore.get_user_by_id(str(inviter_member.user_id))
            inviter_name = 'A team member'
            if inviter_user and inviter_user.email:
                inviter_name = inviter_user.email.split('@')[0]

            EmailService.send_invitation_email(
                to_email=email,
                org_name=org.name,
                inviter_name=inviter_name,
                role_name=target_role.name,
                invitation_token=invitation.token,
                invitation_id=invitation.id,
            )
        except Exception as e:
            logger.error(
                'Failed to send invitation email',
                extra={
                    'invitation_id': invitation.id,
                    'email': email,
                    'error': str(e),
                },
            )
            # Don't fail the invitation creation if email fails
            # The user can still access via direct link

        return invitation