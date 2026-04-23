def get_pr_comments(
        self, pr_number: int, comment_id: int | None = None
    ) -> list[str] | None:
        """Download comments for a specific pull request from Gitlab."""
        url = f'{self.base_url}/merge_requests/{pr_number}/notes'
        params = {'per_page': 100, 'page': 1}
        all_comments = []

        while True:
            response = httpx.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            comments = response.json()
            comments = [
                comment
                for comment in comments
                if comment.get('resolvable', True) and not comment.get('system', True)
            ]

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