async def get_org_info(self) -> dict | None:
        """Get organization info for the current user.

        Lazily loads and caches organization data including:
        - org_id: Current organization ID
        - org_name: Current organization name
        - role: User's role in the organization
        - permissions: List of permission names for the role

        Returns:
            dict with org_id, org_name, role, permissions or None if not available
        """
        if self._org_info_loaded:
            if self._org_id is None:
                return None
            return {
                'org_id': self._org_id,
                'org_name': self._org_name,
                'role': self._role,
                'permissions': self._permissions,
            }

        # Mark as loaded to avoid repeated attempts on failure
        self._org_info_loaded = True

        try:
            # Get user and their current org
            user = await UserStore.get_user_by_id(self.user_id)
            if not user:
                logger.warning(f'User {self.user_id} not found for org info')
                return None

            # Get the current org
            org = await OrgStore.get_org_by_id(user.current_org_id)
            if not org:
                logger.warning(
                    f'Organization {user.current_org_id} not found for user {self.user_id}'
                )
                return None

            # Get user's role in the current org
            role = await get_user_org_role(self.user_id, user.current_org_id)
            role_name = role.name if role else None

            # Get permissions for the role
            permissions: list[str] = []
            if role_name:
                role_permissions = get_role_permissions(role_name)
                permissions = [p.value for p in role_permissions]

            # Cache the results
            self._org_id = str(user.current_org_id)
            self._org_name = org.name
            self._role = role_name
            self._permissions = permissions

            return {
                'org_id': self._org_id,
                'org_name': self._org_name,
                'role': self._role,
                'permissions': self._permissions,
            }
        except Exception as e:
            logger.error(f'Error fetching org info for user {self.user_id}: {e}')
            return None