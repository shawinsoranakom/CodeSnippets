async def create_pull_request(self, data: dict[str, Any] | None = None) -> dict:
        payload: dict[str, Any] = dict(data or {})

        repository = payload.pop('repository', None)
        owner = payload.pop('owner', None)
        repo_name = payload.pop('repo', None)

        if repository and isinstance(repository, str):
            owner, repo_name = self._split_repo(repository)
        else:
            owner = str(owner or self.user_id or '').strip()
            repo_name = str(repo_name or '').strip()

        if not owner or not repo_name:
            raise ValueError(
                'Repository information is required to create a pull request'
            )

        url = self._build_repo_api_url(owner, repo_name, 'pulls')
        response, _ = await self._make_request(
            url,
            payload,
            method=RequestMethod.POST,
        )

        if not isinstance(response, dict):
            raise UnknownException('Unexpected response creating Forgejo pull request')

        if 'number' not in response and 'index' in response:
            response['number'] = response['index']

        if 'html_url' not in response and 'url' in response:
            response['html_url'] = response['url']

        return response