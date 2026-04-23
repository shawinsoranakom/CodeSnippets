async def update_org_member(
        org_id: UUID,
        target_user_id: UUID,
        current_user_id: UUID,
        update_data: OrgMemberUpdate,
    ) -> OrgMemberResponse:
        """Update a member's role in an organization.

        Permission rules:
        - Owners can modify anyone (including other owners), can set any role
        - Admins can modify other admins and users
        - Admins can only set admin or user roles (not owner)

        Args:
            org_id: Organization ID
            target_user_id: User ID of the member to update
            current_user_id: User ID of the requester
            update_data: Update data containing fields to modify

        Returns:
            OrgMemberResponse: The updated member data

        Raises:
            OrgMemberNotFoundError: If requester or target is not a member
            CannotModifySelfError: If trying to modify self
            RoleNotFoundError: If role configuration is invalid
            InvalidRoleError: If new_role_name is not a valid role
            InsufficientPermissionError: If requester lacks permission
            LastOwnerError: If trying to demote the last owner
            MemberUpdateError: If update operation fails
        """
        new_role_name = update_data.role

        # Get current user's membership in the org
        requester_membership = await OrgMemberStore.get_org_member(
            org_id, current_user_id
        )
        if not requester_membership:
            raise OrgMemberNotFoundError(str(org_id), str(current_user_id))

        # Check if trying to modify self
        if str(current_user_id) == str(target_user_id):
            raise CannotModifySelfError('modify')

        # Get target user's membership
        target_membership = await OrgMemberStore.get_org_member(org_id, target_user_id)
        if not target_membership:
            raise OrgMemberNotFoundError(str(org_id), str(target_user_id))

        # Get roles
        requester_role = await RoleStore.get_role_by_id(requester_membership.role_id)
        target_role = await RoleStore.get_role_by_id(target_membership.role_id)

        if not requester_role:
            raise RoleNotFoundError(requester_membership.role_id)
        if not target_role:
            raise RoleNotFoundError(target_membership.role_id)

        # If no role change requested, return current state
        if new_role_name is None:
            user = await UserStore.get_user_by_id(str(target_user_id))
            return OrgMemberResponse(
                user_id=str(target_membership.user_id),
                email=user.email if user else None,
                role_id=target_membership.role_id,
                role=target_role.name,
                role_rank=target_role.rank,
                status=target_membership.status,
            )

        # Validate new role exists
        new_role = await RoleStore.get_role_by_name(new_role_name.lower())
        if not new_role:
            raise InvalidRoleError(new_role_name)

        # Check permission to modify target
        if not OrgMemberService._can_update_member_role(
            requester_role.name, target_role.name, new_role.name
        ):
            raise InsufficientPermissionError(
                'You do not have permission to modify this member'
            )

        # Check if demoting the last owner
        if (
            target_role.name == ROLE_OWNER
            and new_role.name != ROLE_OWNER
            and await OrgMemberService._is_last_owner(org_id, target_user_id)
        ):
            raise LastOwnerError('demote')

        # Perform the update
        updated_member = await OrgMemberStore.update_user_role_in_org(
            org_id, target_user_id, new_role.id
        )
        if not updated_member:
            raise MemberUpdateError('Failed to update member')

        # Get user email for response
        user = await UserStore.get_user_by_id(str(target_user_id))

        return OrgMemberResponse(
            user_id=str(updated_member.user_id),
            email=user.email if user else None,
            role_id=updated_member.role_id,
            role=new_role.name,
            role_rank=new_role.rank,
            status=updated_member.status,
        )