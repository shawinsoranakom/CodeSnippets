async def get_all_repositories(
        self, sort: str, app_mode: AppMode, store_in_background: bool = True
    ) -> list[Repository]:
        """
        Get repositories for the authenticated user, including information about the kind of project.
        Also collects repositories where the kind is "user" and the user is the owner.

        Args:
            sort: The field to sort repositories by
            app_mode: The application mode (OSS or SAAS)

        Returns:
            List[Repository]: A list of repositories for the authenticated user
        """
        MAX_REPOS = 1000
        PER_PAGE = 100  # Maximum allowed by GitLab API
        all_repos: list[dict] = []
        users_personal_projects: list[dict] = []
        page = 1

        url = f'{self.BASE_URL}/projects'
        # Map GitHub's sort values to GitLab's order_by values
        order_by = {
            'pushed': 'last_activity_at',
            'updated': 'last_activity_at',
            'created': 'created_at',
            'full_name': 'name',
        }.get(sort, 'last_activity_at')

        user_id = None
        try:
            user_info = await self.get_user()
            user_id = user_info.id
        except Exception as e:
            logger.warning(f'Could not fetch user id: {e}')

        while len(all_repos) < MAX_REPOS:
            params = {
                'page': str(page),
                'per_page': str(PER_PAGE),
                'order_by': order_by,
                'sort': 'desc',  # GitLab uses sort for direction (asc/desc)
                'membership': 1,  # Use 1 instead of True
            }

            try:
                response, headers = await self._make_request(url, params)

                if not response:  # No more repositories
                    break

                # Process each repository to identify user-owned ones
                for repo in response:
                    namespace = repo.get('namespace', {})
                    kind = namespace.get('kind')
                    owner_id = repo.get('owner', {}).get('id')

                    # Collect user owned personal projects
                    if kind == 'user' and str(owner_id) == str(user_id):
                        users_personal_projects.append(repo)

                    # Add to all repos regardless
                    all_repos.append(repo)

                page += 1

                # Check if we've reached the last page
                link_header = headers.get('Link', '')
                if 'rel="next"' not in link_header:
                    break

            except Exception:
                logger.warning(
                    f'Error fetching repositories on page {page}', exc_info=True
                )
                break

        # Trim to MAX_REPOS if needed and convert to Repository objects
        all_repos = all_repos[:MAX_REPOS]
        repositories = [
            Repository(
                id=str(repo.get('id')),
                full_name=str(repo.get('path_with_namespace')),
                stargazers_count=repo.get('star_count'),
                git_provider=ProviderType.GITLAB,
                is_public=repo.get('visibility') == 'public',
            )
            for repo in all_repos
        ]

        # Store webhook and repository info
        if store_in_background:
            asyncio.create_task(
                self.store_repository_data(users_personal_projects, repositories)
            )
        else:
            await self.store_repository_data(users_personal_projects, repositories)
        return repositories