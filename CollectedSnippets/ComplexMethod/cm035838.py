async def remove_org_member(
        org_id: UUID,
        target_user_id: UUID,
        current_user_id: UUID,
    ) -> tuple[bool, str | None]:
        """Remove a member from an organization.

        Returns:
            Tuple of (success, error_message). If success is True, error_message is None.
        """
        # Get current user's membership in the org
        requester_membership = await OrgMemberStore.get_org_member(
            org_id, current_user_id
        )
        if not requester_membership:
            return False, 'not_a_member'

        # Check if trying to remove self
        if str(current_user_id) == str(target_user_id):
            return False, 'cannot_remove_self'

        # Get target user's membership
        target_membership = await OrgMemberStore.get_org_member(org_id, target_user_id)
        if not target_membership:
            return False, 'member_not_found'

        requester_role = await RoleStore.get_role_by_id(requester_membership.role_id)
        target_role = await RoleStore.get_role_by_id(target_membership.role_id)

        if not requester_role or not target_role:
            return False, 'role_not_found'

        # Check permission based on roles
        if not OrgMemberService._can_remove_member(
            requester_role.name, target_role.name
        ):
            return False, 'insufficient_permission'

        # Check if removing the last owner
        if target_role.name == ROLE_OWNER:
            if await OrgMemberService._is_last_owner(org_id, target_user_id):
                return False, 'cannot_remove_last_owner'

        # Perform the removal
        success = await OrgMemberStore.remove_user_from_org(org_id, target_user_id)
        if not success:
            return False, 'removal_failed'

        # Update user's current_org_id if it points to the org they were removed from
        user = await UserStore.get_user_by_id(str(target_user_id))
        if user and user.current_org_id == org_id:
            # Set current_org_id to personal workspace (org.id == user.id)
            await UserStore.update_current_org(str(target_user_id), target_user_id)

        # If database removal succeeded, also remove from LiteLLM team
        try:
            await LiteLlmManager.remove_user_from_team(str(target_user_id), str(org_id))
            logger.info(
                'Successfully removed user from LiteLLM team',
                extra={
                    'user_id': str(target_user_id),
                    'org_id': str(org_id),
                },
            )
        except Exception as e:
            # Log but don't fail the operation - database removal already succeeded
            # LiteLLM state will be eventually consistent
            logger.warning(
                'Failed to remove user from LiteLLM team',
                extra={
                    'user_id': str(target_user_id),
                    'org_id': str(org_id),
                    'error': str(e),
                },
            )

        return True, None