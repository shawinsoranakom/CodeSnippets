def get_pr_comments(
        self, pr_number: int, comment_id: int | None = None
    ) -> list[str] | None:
        """Download comments for a specific pull request from Github."""
        if self.base_domain == 'github.com':
            url = f'https://api.github.com/repos/{self.owner}/{self.repo}/issues/{pr_number}/comments'
        else:
            url = f'https://{self.base_domain}/api/v3/repos/{self.owner}/{self.repo}/issues/{pr_number}/comments'
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
        }
        params = {'per_page': 100, 'page': 1}
        all_comments = []

        while True:
            response = httpx.get(url, headers=headers, params=params)
            response.raise_for_status()
            comments = response.json()

            if not comments:
                break

            if comment_id is not None:
                matching_comment = next(
                    (
                        comment['body']
                        for comment in comments
                        if comment['id'] == comment_id
                    ),
                    None,
                )
                if matching_comment:
                    return [matching_comment]
            else:
                all_comments.extend([comment['body'] for comment in comments])

            params['page'] += 1

        return all_comments if all_comments else None