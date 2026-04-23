async def get_repositories(self, sort: str, app_mode: AppMode) -> list[Repository]:
        """Get repositories for the authenticated user."""
        MAX_REPOS = 1000

        # Get all projects first
        projects_url = f'{self.base_url}/_apis/projects?api-version=7.1'
        projects_response, _ = await self._make_request(projects_url)
        projects = projects_response.get('value', [])

        all_repos = []

        # For each project, get its repositories
        for project in projects:
            project_name = project.get('name')
            project_enc = self._encode_url_component(project_name)
            repos_url = (
                f'{self.base_url}/{project_enc}/_apis/git/repositories?api-version=7.1'
            )
            repos_response, _ = await self._make_request(repos_url)
            repos = repos_response.get('value', [])

            for repo in repos:
                all_repos.append(
                    {
                        'id': repo.get('id'),
                        'name': repo.get('name'),
                        'project_name': project_name,
                        'updated_date': repo.get('lastUpdateTime'),
                    }
                )

                if len(all_repos) >= MAX_REPOS:
                    break

            if len(all_repos) >= MAX_REPOS:
                break

        # Sort repositories based on the sort parameter
        if sort == 'updated':
            all_repos.sort(key=lambda r: r.get('updated_date', ''), reverse=True)
        elif sort == 'name':
            all_repos.sort(key=lambda r: r.get('name', '').lower())

        return [
            Repository(
                id=str(repo.get('id')),
                full_name=f'{self.organization}/{repo.get("project_name")}/{repo.get("name")}',
                git_provider=ProviderType.AZURE_DEVOPS,
                is_public=False,  # Azure DevOps repos are private by default
            )
            for repo in all_repos[:MAX_REPOS]
        ]