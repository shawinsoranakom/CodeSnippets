async def get_paginated_branches(
        self, repository: str, page: int = 1, per_page: int = 30
    ) -> PaginatedBranchesResponse:  # type: ignore[override]
        owner, repo = self._split_repo(repository)
        url = self._build_repo_api_url(owner, repo, 'branches')
        params = {
            'page': str(page),
            'limit': str(per_page),
        }

        response, headers = await self._make_request(url, params)
        branch_items = response if isinstance(response, list) else []

        branches: list[Branch] = []
        for branch in branch_items:
            commit_info = branch.get('commit') or {}
            commit_sha = (
                commit_info.get('id')
                or commit_info.get('sha')
                or commit_info.get('commit', {}).get('sha')
            )
            branches.append(
                Branch(
                    name=branch.get('name', ''),
                    commit_sha=commit_sha or '',
                    protected=branch.get('protected', False),
                    last_push_date=None,
                )
            )

        link_header = headers.get('Link', '')
        total_count_header = headers.get('X-Total-Count') or headers.get('X-Total')
        total_count = int(total_count_header) if total_count_header else None
        has_next_page = 'rel="next"' in link_header

        return PaginatedBranchesResponse(
            branches=branches,
            has_next_page=has_next_page,
            current_page=page,
            per_page=per_page,
            total_count=total_count,
        )