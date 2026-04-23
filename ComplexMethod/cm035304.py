def get_context_from_external_issues_references(
        self,
        closing_issues: list[str],
        closing_issue_numbers: list[int],
        issue_body: str,
        review_comments: list[str] | None,
        review_threads: list[ReviewThread],
        thread_comments: list[str] | None,
    ) -> list[str]:
        new_issue_references = []

        if issue_body:
            new_issue_references.extend(extract_issue_references(issue_body))

        if review_comments:
            for comment in review_comments:
                new_issue_references.extend(extract_issue_references(comment))

        if review_threads:
            for review_thread in review_threads:
                new_issue_references.extend(
                    extract_issue_references(review_thread.comment)
                )

        if thread_comments:
            for thread_comment in thread_comments:
                new_issue_references.extend(extract_issue_references(thread_comment))

        non_duplicate_references = set(new_issue_references)
        unique_issue_references = non_duplicate_references.difference(
            closing_issue_numbers
        )

        for issue_number in unique_issue_references:
            try:
                url = f'{self.base_url}/issues/{issue_number}'
                response = httpx.get(url, headers=self.headers)
                response.raise_for_status()
                issue_data = response.json()
                issue_body = issue_data.get('description', '')
                if issue_body:
                    closing_issues.append(issue_body)
            except httpx.HTTPError as e:
                logger.warning(f'Failed to fetch issue {issue_number}: {str(e)}')

        return closing_issues