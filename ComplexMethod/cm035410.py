async def get_paginated_repos(
        self,
        page: int,
        per_page: int,
        sort: str,
        installation_id: str | None,
        query: str | None = None,
    ) -> list[Repository]:
        """Get paginated repositories for a specific project.

        Args:
            page: The page number to fetch
            per_page: The number of repositories per page
            sort: The sort field ('pushed', 'updated', 'created', 'full_name')
            installation_id: The project slug to fetch repositories from (as int, will be converted to string)

        Returns:
            A list of Repository objects
        """
        if not installation_id:
            return []

        # Convert installation_id to string for use as project_slug
        project_slug = installation_id

        project_repos_url = f'{self.BASE_URL}/projects/{project_slug}/repos'
        # Calculate start offset from page number (Bitbucket Server uses 0-based start index)
        start = (page - 1) * per_page
        params: dict[str, Any] = {'limit': per_page, 'start': start}
        response, _ = await self._make_request(project_repos_url, params)
        repos = response.get('values', [])
        if query:
            repos = [
                repo
                for repo in repos
                if query.lower() in repo.get('slug', '').lower()
                or query.lower() in repo.get('name', '').lower()
            ]
        formatted_link_header = ''
        if not response.get('isLastPage', True):
            next_page = page + 1
            # Use 'page=' format for frontend compatibility with extractNextPageFromLink
            formatted_link_header = (
                f'<{project_repos_url}?page={next_page}>; rel="next"'
            )
        return [
            await self._parse_repository(repo, link_header=formatted_link_header)
            for repo in repos
        ]