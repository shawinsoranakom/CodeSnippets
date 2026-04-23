async def execute_graphql_query(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> Any:
        """Execute a GraphQL query against the GitLab GraphQL API

        Args:
            query: The GraphQL query string
            variables: Optional variables for the GraphQL query

        Returns:
            The data portion of the GraphQL response
        """
        if variables is None:
            variables = {}
        try:
            async with httpx.AsyncClient(verify=httpx_verify_option()) as client:
                gitlab_headers = await self._get_headers()
                # Add content type header for GraphQL
                gitlab_headers['Content-Type'] = 'application/json'

                payload = {
                    'query': query,
                    'variables': variables if variables is not None else {},
                }

                response = await client.post(
                    self.GRAPHQL_URL, headers=gitlab_headers, json=payload
                )

                if self.refresh and self._has_token_expired(response.status_code):
                    await self.get_latest_token()
                    gitlab_headers = await self._get_headers()
                    gitlab_headers['Content-Type'] = 'application/json'
                    response = await client.post(
                        self.GRAPHQL_URL, headers=gitlab_headers, json=payload
                    )

                response.raise_for_status()
                result = response.json()

                # Check for GraphQL errors
                if 'errors' in result:
                    error_message = result['errors'][0].get(
                        'message', 'Unknown GraphQL error'
                    )
                    raise UnknownException(f'GraphQL error: {error_message}')

                return result.get('data')
        except httpx.HTTPStatusError as e:
            raise self.handle_http_status_error(e)
        except httpx.HTTPError as e:
            raise self.handle_http_error(e)