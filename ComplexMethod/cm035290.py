def get_converted_issues(
        self, issue_numbers: list[int] | None = None, comment_id: int | None = None
    ) -> list[Issue]:
        if not issue_numbers:
            raise ValueError('Unspecified issue numbers')

        all_issues = self.download_issues()
        logger.info(f'Limiting resolving to issues {issue_numbers}.')
        filtered = [
            issue
            for issue in all_issues
            if self._to_int(issue.get('number') or issue.get('index')) in issue_numbers
        ]

        converted: list[Issue] = []
        for issue in filtered:
            if any(issue.get(key) is None for key in ['number', 'title']):
                logger.warning(
                    f'Skipping issue {issue} as it is missing number or title.'
                )
                continue

            issue_number = self._to_int(issue.get('number') or issue.get('index'))
            body = issue.get('body') or ''
            thread_comments = self.get_issue_comments(issue_number, comment_id)

            issue_details = Issue(
                owner=self.owner,
                repo=self.repo,
                number=issue_number,
                title=issue['title'],
                body=body,
                thread_comments=thread_comments,
                review_comments=None,
                review_threads=None,
            )
            converted.append(issue_details)

        return converted