def get_converted_issues(
        self, issue_numbers: list[int] | None = None, comment_id: int | None = None
    ) -> list[Issue]:
        """Download issues from Github.

        Args:
            issue_numbers: The numbers of the issues to download
            comment_id: The ID of a single comment, if provided, otherwise all comments

        Returns:
            List of Github issues.
        """
        if not issue_numbers:
            raise ValueError('Unspecified issue number')

        all_issues = self.download_issues()
        logger.info(f'Limiting resolving to issues {issue_numbers}.')
        all_issues = [
            issue
            for issue in all_issues
            if issue['number'] in issue_numbers and 'pull_request' not in issue
        ]

        if len(issue_numbers) == 1 and not all_issues:
            raise ValueError(f'Issue {issue_numbers[0]} not found')

        converted_issues = []
        for issue in all_issues:
            # Check for required fields (number and title)
            if any([issue.get(key) is None for key in ['number', 'title']]):
                logger.warning(
                    f'Skipping issue {issue} as it is missing number or title.'
                )
                continue

            # Handle empty body by using empty string
            if issue.get('body') is None:
                issue['body'] = ''

            # Get issue thread comments
            thread_comments = self.get_issue_comments(
                issue['number'], comment_id=comment_id
            )
            # Convert empty lists to None for optional fields
            issue_details = Issue(
                owner=self.owner,
                repo=self.repo,
                number=issue['number'],
                title=issue['title'],
                body=issue['body'],
                thread_comments=thread_comments,
                review_comments=None,  # Initialize review comments as None for regular issues
            )

            converted_issues.append(issue_details)

        return converted_issues