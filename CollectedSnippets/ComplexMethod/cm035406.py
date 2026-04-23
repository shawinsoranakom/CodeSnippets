async def search_repositories(
        self,
        query: str,
        per_page: int,
        sort: str,
        order: str,
        public: bool,
        app_mode: AppMode,
    ) -> list[Repository]:
        url = f'{self.BASE_URL}/search/repositories'
        params = {
            'per_page': per_page,
            'sort': sort,
            'order': order,
        }

        if public:
            url_parts = query.split('/')
            if len(url_parts) < 4:
                return []

            org = url_parts[3]
            repo_name = url_parts[4]
            # Add is:public to the query to ensure we only search for public repositories
            params['q'] = f'in:name {org}/{repo_name} is:public'

        # Handle private repository searches
        if not public and '/' in query:
            org, repo_query = query.split('/', 1)
            query_with_user = f'org:{org} in:name {repo_query}'
            params['q'] = query_with_user
        elif not public:
            # Expand search scope to include user's repositories and organizations the app has access to
            user = await self.get_user()
            if app_mode == AppMode.SAAS:
                user_orgs = await self.get_organizations_from_installations()
            else:
                user_orgs = await self.get_user_organizations()

            # Search in user repos and org repos separately
            all_repos = []

            # Search in user repositories
            user_query = f'in:name {query} user:{user.login}'
            user_params = params.copy()
            user_params['q'] = user_query

            try:
                user_response, _ = await self._make_request(url, user_params)
                user_items = user_response.get('items', [])
                all_repos.extend(user_items)
            except Exception as e:
                logger.warning(f'User search failed: {e}')

            # Search for repos named "query" in each organization
            for org in user_orgs:
                org_query = f'{query} org:{org}'
                org_params = params.copy()
                org_params['q'] = org_query

                try:
                    org_response, _ = await self._make_request(url, org_params)
                    org_items = org_response.get('items', [])
                    all_repos.extend(org_items)
                except Exception as e:
                    logger.warning(f'Org {org} search failed: {e}')

            # Also search for top repos from orgs that match the query name
            for org in user_orgs:
                if self._fuzzy_match_org_name(query, org):
                    org_repos_query = f'org:{org}'
                    org_repos_params = params.copy()
                    org_repos_params['q'] = org_repos_query
                    org_repos_params['sort'] = 'stars'
                    org_repos_params['per_page'] = 2  # Limit to first 2 repos

                    try:
                        org_repos_response, _ = await self._make_request(
                            url, org_repos_params
                        )
                        org_repo_items = org_repos_response.get('items', [])
                        all_repos.extend(org_repo_items)
                    except Exception as e:
                        logger.warning(f'Org repos search for {org} failed: {e}')

            return [self._parse_repository(repo) for repo in all_repos]

        # Default case (public search or slash query)
        response, _ = await self._make_request(url, params)
        repo_items = response.get('items', [])
        return [self._parse_repository(repo) for repo in repo_items]