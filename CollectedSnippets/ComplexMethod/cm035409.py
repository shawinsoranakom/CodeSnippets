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
            try:
                parsed_url = urlparse(query)
                path_segments = [
                    segment for segment in parsed_url.path.split('/') if segment
                ]

                if 'projects' in path_segments:
                    idx = path_segments.index('projects')
                    if (
                        len(path_segments) > idx + 2
                        and path_segments[idx + 1]
                        and path_segments[idx + 2] == 'repos'
                    ):
                        project_key = path_segments[idx + 1]
                        repo_name = (
                            path_segments[idx + 3]
                            if len(path_segments) > idx + 3
                            else ''
                        )
                    elif len(path_segments) > idx + 2:
                        project_key = path_segments[idx + 1]
                        repo_name = path_segments[idx + 2]
                    else:
                        project_key = ''
                        repo_name = ''
                else:
                    project_key = path_segments[0] if len(path_segments) >= 1 else ''
                    repo_name = path_segments[1] if len(path_segments) >= 2 else ''

                if project_key and repo_name:
                    repo = await self.get_repository_details_from_repo_name(
                        f'{project_key}/{repo_name}'
                    )
                    repositories.append(repo)
            except (ValueError, IndexError):
                pass

            return repositories

        MAX_REPOS = 1000
        # Search for repos once project prefix exists
        if '/' in query:
            project_slug, repo_query = query.split('/', 1)
            project_repos_url = f'{self.BASE_URL}/projects/{project_slug}/repos'
            raw_repos = await self._fetch_paginated_data(
                project_repos_url, {'limit': per_page}, MAX_REPOS
            )
            if repo_query:
                raw_repos = [
                    r
                    for r in raw_repos
                    if repo_query.lower() in r.get('slug', '').lower()
                    or repo_query.lower() in r.get('name', '').lower()
                ]
            return [await self._parse_repository(repo) for repo in raw_repos]

        # No '/' in query, search across all projects
        all_projects = await self.get_installations()
        for project_key in all_projects:
            try:
                repos = await self.get_paginated_repos(
                    1, per_page, sort, project_key, query
                )
                repositories.extend(repos)
            except Exception:
                continue
        return repositories