def get_issue_comments(
        self, issue_number: int, comment_id: int | None = None
    ) -> list[str] | None:
        url = f'{self.get_download_url()}/{issue_number}/comments'
        page = 1
        params = {'limit': '50', 'page': str(page)}
        all_comments: list[str] = []

        while True:
            response = httpx.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            comments = response.json()

            if not comments:
                break

            if comment_id is not None:
                matching_comment = next(
                    (
                        comment['body']
                        for comment in comments
                        if self._to_int(comment.get('id')) == comment_id
                    ),
                    None,
                )
                if matching_comment:
                    return [matching_comment]
            else:
                all_comments.extend(
                    comment['body'] for comment in comments if comment.get('body')
                )

            page += 1
            params = {'limit': '50', 'page': str(page)}

        return all_comments if all_comments else None