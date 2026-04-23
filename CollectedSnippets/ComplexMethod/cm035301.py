def get_issue_comments(
        self, issue_number: int, comment_id: int | None = None
    ) -> list[str] | None:
        """Download comments for a specific issue from Gitlab."""
        url = f'{self.download_url}/{issue_number}/notes'
        params = {'per_page': 100, 'page': 1}
        all_comments = []

        while True:
            response = httpx.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            comments = response.json()

            if not comments:
                break

            if comment_id:
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