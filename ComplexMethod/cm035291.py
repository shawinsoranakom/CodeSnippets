def get_pr_comments(
        self, pr_number: int, comment_id: int | None = None
    ) -> list[str] | None:
        url = f'{self.get_base_url()}/pulls/{pr_number}/comments'
        page = 1
        params = {'limit': '50', 'page': str(page)}
        collected: list[str] = []

        while True:
            response = httpx.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            comments = response.json()

            if not comments:
                break

            filtered = [
                comment for comment in comments if not comment.get('is_system', False)
            ]

            if comment_id is not None:
                matching = next(
                    (
                        comment['body']
                        for comment in filtered
                        if self._to_int(comment.get('id')) == comment_id
                    ),
                    None,
                )
                if matching:
                    return [matching]
            else:
                collected.extend(
                    comment['body'] for comment in filtered if comment.get('body')
                )

            page += 1
            params = {'limit': '50', 'page': str(page)}

        return collected if collected else None