def get_converted_issues(
        self, issue_numbers: list[int] | None = None, comment_id: int | None = None
    ) -> list[Issue]:
        if not issue_numbers:
            raise ValueError('Unspecified issue numbers')

        response = httpx.get(self.download_url, headers=self.headers)
        response.raise_for_status()
        all_prs = response.json()

        logger.info(f'Limiting resolving to PRs {issue_numbers}.')
        filtered = [
            pr
            for pr in all_prs
            if self._to_int(pr.get('number') or pr.get('index')) in issue_numbers
        ]

        converted: list[Issue] = []
        for pr in filtered:
            if any(pr.get(key) is None for key in ['number', 'title']):
                logger.warning(f'Skipping PR {pr} as it is missing number or title.')
                continue

            body = pr.get('body') or ''
            pr_number = self._to_int(pr.get('number') or pr.get('index', 0))
            (
                closing_issues,
                closing_issue_numbers,
                review_comments,
                review_threads,
                thread_ids,
            ) = self.download_pr_metadata(pr_number, comment_id)
            head_branch = (pr.get('head') or {}).get('ref')
            thread_comments = self.get_pr_comments(pr_number, comment_id)

            closing_issues = self.get_context_from_external_issues_references(
                closing_issues,
                closing_issue_numbers,
                body,
                review_comments,
                review_threads,
                thread_comments,
            )

            issue_details = Issue(
                owner=self.owner,
                repo=self.repo,
                number=pr_number,
                title=pr['title'],
                body=body,
                closing_issues=closing_issues,
                review_comments=review_comments,
                review_threads=review_threads,
                thread_ids=thread_ids,
                head_branch=head_branch,
                thread_comments=thread_comments,
            )

            converted.append(issue_details)

        return converted