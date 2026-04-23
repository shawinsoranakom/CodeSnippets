async def update_org_with_permissions(
        org_id: UUID,
        update_data: OrgUpdate,
        user_id: str,
    ) -> Org:
        """
        Update organization with permission checks for LLM settings.

        Args:
            org_id: Organization UUID to update
            update_data: Organization update data from request
            user_id: ID of the user requesting the update

        Returns:
            Org: The updated organization object

        Raises:
            ValueError: If organization not found
            PermissionError: If user is not a member, or lacks admin/owner role for LLM settings
            OrgNameExistsError: If new name already exists for another organization
            OrgDatabaseError: If database update fails
        """
        logger.info(
            'Updating organization with permission checks',
            extra={
                'org_id': str(org_id),
                'user_id': user_id,
                'has_update_data': update_data is not None,
            },
        )

        # Validate organization exists
        existing_org = await OrgStore.get_org_by_id(org_id)
        if not existing_org:
            raise ValueError(f'Organization with ID {org_id} not found')

        # Check if user is a member of this organization
        if not await OrgService.is_org_member(user_id, org_id):
            logger.warning(
                'Non-member attempted to update organization',
                extra={
                    'user_id': user_id,
                    'org_id': str(org_id),
                },
            )
            raise PermissionError(
                'User must be a member of the organization to update it'
            )

        # Check if name is being updated and validate uniqueness
        if update_data.name is not None:
            # Check if new name conflicts with another org
            existing_org_with_name = await OrgStore.get_org_by_name(update_data.name)
            if (
                existing_org_with_name is not None
                and existing_org_with_name.id != org_id
            ):
                logger.warning(
                    'Attempted to update organization with duplicate name',
                    extra={
                        'user_id': user_id,
                        'org_id': str(org_id),
                        'attempted_name': update_data.name,
                    },
                )
                raise OrgNameExistsError(update_data.name)

        if not update_data.has_updates():
            logger.info(
                'No fields to update',
                extra={'org_id': str(org_id), 'user_id': user_id},
            )
            return existing_org

        restricted_fields = update_data.restricted_fields()
        if restricted_fields and not await OrgService.has_admin_or_owner_role(
            user_id, org_id
        ):
            logger.warning(
                'Insufficient role for restricted organization settings update',
                extra={
                    'user_id': user_id,
                    'org_id': str(org_id),
                    'restricted_fields': sorted(restricted_fields),
                },
            )
            raise PermissionError(
                'Admin or owner role required to update organization default settings'
            )

        try:
            updated_org = await OrgStore.update_org(org_id, update_data, user_id)
            if not updated_org:
                raise OrgDatabaseError('Failed to update organization in database')

            logger.info(
                'Organization updated successfully',
                extra={
                    'org_id': str(org_id),
                    'user_id': user_id,
                    'updated_fields': sorted(update_data.updated_fields()),
                },
            )

            return updated_org

        except Exception as e:
            logger.error(
                'Failed to update organization',
                extra={
                    'org_id': str(org_id),
                    'user_id': user_id,
                    'error': str(e),
                },
            )
            raise OrgDatabaseError(f'Failed to update organization: {str(e)}')