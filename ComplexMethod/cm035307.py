def get_converted_issues(
        self, issue_numbers: list[int] | None = None, comment_id: int | None = None
    ) -> list[Issue]:
        """Get converted issues.

        Args:
            issue_numbers: List of issue numbers
            comment_id: The comment ID

        Returns:
            A list of converted issues
        """
        if not issue_numbers:
            raise ValueError('Unspecified issue numbers')

        all_issues = self.download_issues()
        logger.info(f'Limiting resolving to issues {issue_numbers}.')
        all_issues = [issue for issue in all_issues if issue.get('id') in issue_numbers]

        converted_issues = []
        for issue in all_issues:
            # For PRs, body can be None
            if any([issue.get(key) is None for key in ['id', 'title']]):
                logger.warning(f'Skipping #{issue} as it is missing id or title.')
                continue

            # Handle None body for PRs
            body = (
                issue.get('content', {}).get('raw', '')
                if issue.get('content') is not None
                else ''
            )

            # Placeholder for PR metadata
            closing_issues: list[str] = []
            review_comments: list[str] = []
            review_threads: list[ReviewThread] = []
            thread_ids: list[str] = []
            head_branch = issue.get('source', {}).get('branch', {}).get('name', '')
            thread_comments: list[str] = []

            issue_details = Issue(
                owner=self.owner,
                repo=self.repo,
                number=issue['id'],
                title=issue['title'],
                body=body,
                closing_issues=closing_issues,
                review_comments=review_comments,
                review_threads=review_threads,
                thread_ids=thread_ids,
                head_branch=head_branch,
                thread_comments=thread_comments,
            )

            converted_issues.append(issue_details)

        return converted_issues