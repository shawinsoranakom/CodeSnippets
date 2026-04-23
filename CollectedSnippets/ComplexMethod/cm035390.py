async def get_paginated_repos(
        self,
        page: int,
        per_page: int,
        sort: str,
        installation_id: str | None,
        query: str | None = None,
    ) -> list[Repository]:
        """Get paginated repositories for a specific workspace.

        Args:
            page: The page number to fetch
            per_page: The number of repositories per page
            sort: The sort field ('pushed', 'updated', 'created', 'full_name')
            installation_id: The workspace slug to fetch repositories from (as int, will be converted to string)

        Returns:
            A list of Repository objects
        """
        if not installation_id:
            return []

        # Convert installation_id to string for use as workspace_slug
        workspace_slug = installation_id
        workspace_repos_url = f'{self.BASE_URL}/repositories/{workspace_slug}'

        # Map sort parameter to Bitbucket API compatible values
        bitbucket_sort = sort
        if sort == 'pushed':
            # Bitbucket doesn't support 'pushed', use 'updated_on' instead
            bitbucket_sort = '-updated_on'  # Use negative prefix for descending order
        elif sort == 'updated':
            bitbucket_sort = '-updated_on'
        elif sort == 'created':
            bitbucket_sort = '-created_on'
        elif sort == 'full_name':
            bitbucket_sort = 'name'  # Bitbucket uses 'name' not 'full_name'
        else:
            # Default to most recently updated first
            bitbucket_sort = '-updated_on'

        params = {
            'pagelen': per_page,
            'page': page,
            'sort': bitbucket_sort,
        }

        if query:
            params['q'] = f'name~"{query}"'

        response, headers = await self._make_request(workspace_repos_url, params)

        # Extract repositories from the response
        repos = response.get('values', [])

        # Extract next URL from response
        next_link = response.get('next', '')

        # Format the link header in a way that the frontend can understand
        # The frontend expects a format like: <url>; rel="next"
        # where the URL contains a page parameter
        formatted_link_header = ''
        if next_link:
            # Extract the page number from the next URL if possible
            page_match = re.search(r'[?&]page=(\d+)', next_link)
            if page_match:
                next_page = page_match.group(1)
                # Format it in a way that extractNextPageFromLink in frontend can parse
                formatted_link_header = (
                    f'<{workspace_repos_url}?page={next_page}>; rel="next"'
                )
            else:
                # If we can't extract the page, just use the next URL as is
                formatted_link_header = f'<{next_link}>; rel="next"'

        repositories = [
            self._parse_repository(repo, link_header=formatted_link_header)
            for repo in repos
        ]

        return repositories