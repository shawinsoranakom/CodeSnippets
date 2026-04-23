async def get_org_members(
        org_id: UUID,
        current_user_id: UUID,
        page_id: str | None = None,
        limit: int = 10,
        email_filter: str | None = None,
    ) -> tuple[bool, str | None, OrgMemberPage | None]:
        """Get organization members with authorization check.

        Args:
            org_id: Organization UUID.
            current_user_id: Requesting user's UUID.
            page_id: Offset encoded as string (e.g., "0", "10", "20").
            limit: Items per page (default 10).
            email_filter: Optional case-insensitive partial email match.

        Returns:
            Tuple of (success, error_code, data). If success is True, error_code is None.
        """
        # Verify current user is a member of the organization
        requester_membership = await OrgMemberStore.get_org_member(
            org_id, current_user_id
        )
        if not requester_membership:
            return False, 'not_a_member', None

        # Parse page_id to get offset (page_id is offset encoded as string)
        offset = 0
        if page_id is not None:
            try:
                offset = int(page_id)
                if offset < 0:
                    return False, 'invalid_page_id', None
            except ValueError:
                return False, 'invalid_page_id', None

        # Call store to get paginated members
        members, _ = await OrgMemberStore.get_org_members_paginated(
            org_id=org_id,
            offset=offset,
            limit=limit,
            email_filter=email_filter,
        )

        # Transform data to response format
        items = []
        for member in members:
            # Access user and role relationships (eagerly loaded)
            user = member.user
            role = member.role

            items.append(
                OrgMemberResponse(
                    user_id=str(member.user_id),
                    email=user.email if user else None,
                    role_id=member.role_id,
                    role=role.name if role else '',
                    role_rank=role.rank if role else 0,
                    status=member.status,
                )
            )

        # Calculate current page (1-indexed)
        current_page = (offset // limit) + 1

        return (
            True,
            None,
            OrgMemberPage(
                items=items,
                current_page=current_page,
                per_page=limit,
            ),
        )