async def create_invitations_batch(
        org_id: UUID,
        emails: list[str],
        role_name: str,
        inviter_id: UUID,
    ) -> tuple[list[OrgInvitation], list[tuple[str, str]]]:
        """Create multiple organization invitations concurrently.

        Validates permissions once upfront, then creates invitations in parallel.

        Args:
            org_id: Organization UUID
            emails: List of invitee email addresses
            role_name: Role to assign on acceptance (owner, admin, member)
            inviter_id: User ID of the person creating the invitations

        Returns:
            Tuple of (successful_invitations, failed_emails_with_errors)

        Raises:
            ValueError: If organization or role not found
            InsufficientPermissionError: If inviter lacks permission
        """
        logger.info(
            'Creating batch organization invitations',
            extra={
                'org_id': str(org_id),
                'email_count': len(emails),
                'role_name': role_name,
                'inviter_id': str(inviter_id),
            },
        )

        # Step 1: Validate permissions upfront (shared for all emails)
        org = await OrgStore.get_org_by_id(org_id)
        if not org:
            raise ValueError(f'Organization {org_id} not found')

        if str(org_id) == str(inviter_id):
            raise InsufficientPermissionError(
                'Cannot invite users to a personal workspace'
            )

        inviter_member = await OrgMemberStore.get_org_member(org_id, inviter_id)
        if not inviter_member:
            raise InsufficientPermissionError(
                'You are not a member of this organization'
            )

        inviter_role = await RoleStore.get_role_by_id(inviter_member.role_id)
        if not inviter_role or inviter_role.name not in [ROLE_OWNER, ROLE_ADMIN]:
            raise InsufficientPermissionError('Only owners and admins can invite users')

        role_name_lower = role_name.lower()
        if role_name_lower == ROLE_OWNER and inviter_role.name != ROLE_OWNER:
            raise InsufficientPermissionError('Only owners can invite with owner role')

        target_role = await RoleStore.get_role_by_name(role_name_lower)
        if not target_role:
            raise ValueError(f'Invalid role: {role_name}')

        # Step 2: Create invitations concurrently
        async def create_single(
            email: str,
        ) -> tuple[str, OrgInvitation | None, str | None]:
            """Create single invitation, return (email, invitation, error)."""
            try:
                invitation = await OrgInvitationService.create_invitation(
                    org_id=org_id,
                    email=email,
                    role_name=role_name,
                    inviter_id=inviter_id,
                )
                return (email, invitation, None)
            except (UserAlreadyMemberError, ValueError) as e:
                return (email, None, str(e))

        results = await asyncio.gather(*[create_single(email) for email in emails])

        # Step 3: Separate successes and failures
        successful: list[OrgInvitation] = []
        failed: list[tuple[str, str]] = []
        for email, invitation, error in results:
            if invitation:
                successful.append(invitation)
            elif error:
                failed.append((email, error))

        logger.info(
            'Batch invitation creation completed',
            extra={
                'org_id': str(org_id),
                'successful': len(successful),
                'failed': len(failed),
            },
        )

        return successful, failed