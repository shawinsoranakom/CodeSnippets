async def check_user_has_admin_access_to_resource(
        self, resource_type: GitLabResourceType, resource_id: str
    ) -> tuple[bool, WebhookStatus | None]:
        """
        Check if the user has admin access to resource (is either an owner or maintainer)

        Args:
            resource_type: The type of resource
            resource_id: The ID of the resource to check

        Returns:
            tuple[bool, str]: A tuple containing:
                - bool: True if the user has admin access to the resource (owner or maintainer), False otherwise
                - str: A reason message explaining the result
        """

        # For groups, we need to check if the user is an owner or maintainer
        if resource_type == GitLabResourceType.GROUP:
            url = f'{self.BASE_URL}/groups/{resource_id}/members/all'
            try:
                response, _ = await self._make_request(url)
                # Check if the current user is in the members list with access level >= 40 (Maintainer or Owner)

                exists = False
                if response:
                    current_user = await self.get_user()
                    user_id = current_user.id
                    for member in response:
                        if (
                            str(member.get('id')) == str(user_id)
                            and member.get('access_level', 0) >= 40
                        ):
                            exists = True
                return exists, None
            except RateLimitError:
                return False, WebhookStatus.RATE_LIMITED
            except Exception:
                return False, WebhookStatus.INVALID

        # For projects, we need to check if the user has maintainer or owner access
        else:
            url = f'{self.BASE_URL}/projects/{resource_id}/members/all'
            try:
                response, _ = await self._make_request(url)
                exists = False
                # Check if the current user is in the members list with access level >= 40 (Maintainer)
                if response:
                    current_user = await self.get_user()
                    user_id = current_user.id
                    for member in response:
                        if (
                            str(member.get('id')) == str(user_id)
                            and member.get('access_level', 0) >= 40
                        ):
                            exists = True
                return exists, None
            except RateLimitError:
                return False, WebhookStatus.RATE_LIMITED
            except Exception:
                logger.warning('Admin access check failed', exc_info=True)
                return False, WebhookStatus.INVALID