async def create_pr(
        self,
        repo_name: str,
        source_branch: str,
        target_branch: str,
        title: str,
        body: str | None = None,
        draft: bool = False,
    ) -> str:
        """Creates a pull request in Bitbucket data center.

        Args:
            repo_name: The repository name in the format "project/repo"
            source_branch: The source branch name
            target_branch: The target branch name
            title: The title of the pull request
            body: The description of the pull request
            draft: Whether to create a draft pull request

        Returns:
            The URL of the created pull request
        """
        owner, repo = self._extract_owner_and_repo(repo_name)
        repo_base = self._repo_api_base(owner, repo)

        payload: dict[str, Any]

        url = f'{repo_base}/pull-requests'
        payload = {
            'title': title,
            'description': body or '',
            'fromRef': {
                'id': f'refs/heads/{source_branch}',
                'repository': {'slug': repo, 'project': {'key': owner}},
            },
            'toRef': {
                'id': f'refs/heads/{target_branch}',
                'repository': {'slug': repo, 'project': {'key': owner}},
            },
        }

        data, _ = await self._make_request(
            url=url, params=payload, method=RequestMethod.POST
        )

        # Return the URL to the pull request
        links = data.get('links', {}) if isinstance(data, dict) else {}

        if isinstance(links, dict):
            html_link = links.get('html')
            if isinstance(html_link, dict):
                href = html_link.get('href')
                if href:
                    return href
            if isinstance(html_link, list) and html_link:
                href = html_link[0].get('href')
                if href:
                    return href
            self_link = links.get('self')
            if isinstance(self_link, dict):
                href = self_link.get('href')
                if href:
                    return href
            if isinstance(self_link, list) and self_link:
                href = self_link[0].get('href')
                if href:
                    return href

        return ''