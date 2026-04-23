async def install_webhook(
        self,
        resource_type: GitLabResourceType,
        resource_id: str,
        webhook_name: str,
        webhook_url: str,
        webhook_secret: str,
        webhook_uuid: str,
        scopes: list[str],
    ) -> tuple[str | None, WebhookStatus | None]:
        """
        Install webhook for user's group or project

        Args:
            resource_type: The type of resource
            resource_id: The ID of the resource to check
            webhook_secret: Webhook secret that is used to verify payload
            webhook_name: Name of webhook
            webhook_url: Webhook URL
            scopes: activity webhook listens for

        Returns:
            tuple[bool, str]: A tuple containing:
                - bool: True if installation was successful, False otherwise
                - str: A reason message explaining the result
        """

        description = 'Cloud OpenHands Resolver'

        # Set up webhook parameters
        webhook_data = {
            'url': webhook_url,
            'name': webhook_name,
            'enable_ssl_verification': True,
            'token': webhook_secret,
            'description': description,
        }

        for scope in scopes:
            webhook_data[scope] = True

        # Add custom headers with user id
        if self.external_auth_id:
            webhook_data['custom_headers'] = [
                {'key': 'X-OpenHands-User-ID', 'value': self.external_auth_id},
                {'key': 'X-OpenHands-Webhook-ID', 'value': webhook_uuid},
            ]

        if resource_type == GitLabResourceType.GROUP:
            url = f'{self.BASE_URL}/groups/{resource_id}/hooks'
        else:
            url = f'{self.BASE_URL}/projects/{resource_id}/hooks'

        try:
            # Make the API request
            response, _ = await self._make_request(
                url=url, params=webhook_data, method=RequestMethod.POST
            )

            if response and 'id' in response:
                return str(response['id']), None

            # Check if the webhook was created successfully
            return None, None

        except RateLimitError:
            return None, WebhookStatus.RATE_LIMITED
        except Exception:
            logger.warning('Webhook installation failed', exc_info=True)
            return None, WebhookStatus.INVALID