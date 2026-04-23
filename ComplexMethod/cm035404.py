async def search_branches(
        self, repository: str, query: str, per_page: int = 30
    ) -> list[Branch]:
        """Search branches by name using GitHub GraphQL with a partial query."""
        # Require a non-empty query
        if not query:
            return []

        # Clamp per_page to GitHub GraphQL limits
        per_page = min(max(per_page, 1), 100)

        # Extract owner and repo name from the repository string
        parts = repository.split('/')
        if len(parts) < 2:
            return []
        owner, name = parts[-2], parts[-1]

        variables = {
            'owner': owner,
            'name': name,
            'query': query or '',
            'perPage': per_page,
        }

        try:
            result = await self.execute_graphql_query(
                search_branches_graphql_query, variables
            )
        except Exception as e:
            logger.warning(f'Failed to search for branches: {e}')
            # Fallback to empty result on any GraphQL error
            return []

        repo = result.get('data', {}).get('repository')
        if not repo or not repo.get('refs'):
            return []

        branches: list[Branch] = []
        for node in repo['refs'].get('nodes', []):
            bname = node.get('name') or ''
            target = node.get('target') or {}
            typename = target.get('__typename')
            commit_sha = ''
            last_push_date = None
            if typename == 'Commit':
                commit_sha = target.get('oid', '') or ''
                last_push_date = target.get('committedDate')

            protected = node.get('branchProtectionRule') is not None

            branches.append(
                Branch(
                    name=bname,
                    commit_sha=commit_sha,
                    protected=protected,
                    last_push_date=last_push_date,
                )
            )

        return branches