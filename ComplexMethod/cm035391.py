async def get_all_repositories(
        self, sort: str, app_mode: AppMode
    ) -> list[Repository]:
        """Get repositories for the authenticated user using workspaces endpoint.

        This method gets all repositories (both public and private) that the user has access to
        by iterating through their workspaces and fetching repositories from each workspace.
        This approach is more comprehensive and efficient than the previous implementation
        that made separate calls for public and private repositories.
        """
        MAX_REPOS = 1000
        PER_PAGE = 100  # Maximum allowed by Bitbucket API
        repositories: list[Repository] = []

        # Get user's workspaces with pagination
        workspaces_url = f'{self.BASE_URL}/workspaces'
        workspaces = await self._fetch_paginated_data(workspaces_url, {}, MAX_REPOS)

        for workspace in workspaces:
            workspace_slug = workspace.get('slug')
            if not workspace_slug:
                continue

            # Get repositories for this workspace with pagination
            workspace_repos_url = f'{self.BASE_URL}/repositories/{workspace_slug}'

            # Map sort parameter to Bitbucket API compatible values and ensure descending order
            # to show most recently changed repos at the top
            bitbucket_sort = sort
            if sort == 'pushed':
                # Bitbucket doesn't support 'pushed', use 'updated_on' instead
                bitbucket_sort = (
                    '-updated_on'  # Use negative prefix for descending order
                )
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
                'pagelen': PER_PAGE,
                'sort': bitbucket_sort,
            }

            # Fetch all repositories for this workspace with pagination
            workspace_repos = await self._fetch_paginated_data(
                workspace_repos_url, params, MAX_REPOS - len(repositories)
            )

            for repo in workspace_repos:
                repositories.append(self._parse_repository(repo))

                # Stop if we've reached the maximum number of repositories
                if len(repositories) >= MAX_REPOS:
                    break

            # Stop if we've reached the maximum number of repositories
            if len(repositories) >= MAX_REPOS:
                break

        return repositories