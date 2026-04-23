def get_converted_issues(
        self, issue_numbers: list[int] | None = None, comment_id: int | None = None
    ) -> list[Issue]:
        if not issue_numbers:
            raise ValueError('Unspecified issue numbers')

        all_issues = self.download_issues()
        logger.info(f'Limiting resolving to issues {issue_numbers}.')
        all_issues = [issue for issue in all_issues if issue['number'] in issue_numbers]

        converted_issues = []
        for issue in all_issues:
            # For PRs, body can be None
            if any([issue.get(key) is None for key in ['number', 'title']]):
                logger.warning(f'Skipping #{issue} as it is missing number or title.')
                continue

            # Handle None body for PRs
            body = issue.get('body') if issue.get('body') is not None else ''
            (
                closing_issues,
                closing_issues_numbers,
                review_comments,
                review_threads,
                thread_ids,
            ) = self.download_pr_metadata(issue['number'], comment_id=comment_id)
            head_branch = issue['head']['ref']

            # Get PR thread comments
            thread_comments = self.get_pr_comments(
                issue['number'], comment_id=comment_id
            )

            closing_issues = self.get_context_from_external_issues_references(
                closing_issues,
                closing_issues_numbers,
                body,
                review_comments,
                review_threads,
                thread_comments,
            )

            issue_details = Issue(
                owner=self.owner,
                repo=self.repo,
                number=issue['number'],
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