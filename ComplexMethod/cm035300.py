def get_converted_issues(
        self, issue_numbers: list[int] | None = None, comment_id: int | None = None
    ) -> list[Issue]:
        """Download issues from Gitlab.

        Args:
            issue_numbers: The numbers of the issues to download
            comment_id: The ID of a single comment, if provided, otherwise all comments

        Returns:
            List of Gitlab issues.
        """
        if not issue_numbers:
            raise ValueError('Unspecified issue number')

        all_issues = self.download_issues()
        logger.info(f'Limiting resolving to issues {issue_numbers}.')
        all_issues = [
            issue
            for issue in all_issues
            # if issue['iid'] in issue_numbers and issue['merge_requests_count'] == 0
            if issue['iid'] in issue_numbers  # TODO for testing
        ]

        if len(issue_numbers) == 1 and not all_issues:
            raise ValueError(f'Issue {issue_numbers[0]} not found')

        converted_issues = []
        for issue in all_issues:
            if any([issue.get(key) is None for key in ['iid', 'title']]):
                logger.warning(f'Skipping issue {issue} as it is missing iid or title.')
                continue

            # Handle empty body by using empty string
            if issue.get('description') is None:
                issue['description'] = ''

            # Get issue thread comments
            thread_comments = self.get_issue_comments(
                issue['iid'], comment_id=comment_id
            )
            # Convert empty lists to None for optional fields
            issue_details = Issue(
                owner=self.owner,
                repo=self.repo,
                number=issue['iid'],
                title=issue['title'],
                body=issue['description'],
                thread_comments=thread_comments,
                review_comments=None,  # Initialize review comments as None for regular issues
            )

            converted_issues.append(issue_details)

        return converted_issues