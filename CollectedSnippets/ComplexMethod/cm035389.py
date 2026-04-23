async def search_repositories(
        self,
        query: str,
        per_page: int,
        sort: str,
        order: str,
        public: bool,
        app_mode: AppMode,
    ) -> list[Repository]:
        """Search for repositories."""
        repositories = []

        if public:
            # Extract workspace and repo from URL using robust URL parsing
            # URL format: https://{domain}/{workspace}/{repo}/{additional_params}
            try:
                parsed_url = urlparse(query)
                # Remove leading slash and split path into segments
                path_segments = [
                    segment for segment in parsed_url.path.split('/') if segment
                ]

                # We need at least 2 path segments: workspace and repo
                if len(path_segments) >= 2:
                    workspace_slug = path_segments[0]
                    repo_name = path_segments[1]

                    repo = await self.get_repository_details_from_repo_name(
                        f'{workspace_slug}/{repo_name}'
                    )
                    repositories.append(repo)
            except (ValueError, IndexError):
                # If URL parsing fails or doesn't have expected structure,
                # return empty list for public search
                pass

            return repositories

        # Search for repos once workspace prefix exists
        if '/' in query:
            workspace_slug, repo_query = query.split('/', 1)
            return await self.get_paginated_repos(
                1, per_page, sort, workspace_slug, repo_query
            )

        all_installations = await self.get_installations()

        # Workspace prefix isn't complete. Search workspace names and repos underneath each workspace
        matching_workspace_slugs = [
            installation for installation in all_installations if query in installation
        ]
        for workspace_slug in matching_workspace_slugs:
            # Get repositories where query matches workspace name
            try:
                repos = await self.get_paginated_repos(
                    1, per_page, sort, workspace_slug
                )
                repositories.extend(repos)
            except Exception:
                continue

        for workspace_slug in all_installations:
            # Get repositories in all workspaces where query matches repo name
            try:
                repos = await self.get_paginated_repos(
                    1, per_page, sort, workspace_slug, query
                )
                repositories.extend(repos)
            except Exception:
                continue

        return repositories