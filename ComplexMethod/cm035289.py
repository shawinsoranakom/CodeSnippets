def get_context_from_external_issues_references(
        self,
        closing_issues: list[str],
        closing_issue_numbers: list[int],
        issue_body: str,
        review_comments: list[str] | None,
        review_threads: list[ReviewThread],
        thread_comments: list[str] | None,
    ) -> list[str]:
        new_references: list[int] = []

        if issue_body:
            new_references.extend(extract_issue_references(issue_body))

        if review_comments:
            for comment in review_comments:
                new_references.extend(extract_issue_references(comment))

        if review_threads:
            for thread in review_threads:
                new_references.extend(extract_issue_references(thread.comment))

        if thread_comments:
            for thread_comment in thread_comments:
                new_references.extend(extract_issue_references(thread_comment))

        unique_ids = set(new_references).difference(closing_issue_numbers)

        for issue_number in unique_ids:
            try:
                response = httpx.get(
                    f'{self.get_download_url()}/{issue_number}',
                    headers=self.headers,
                )
                response.raise_for_status()
                issue_data = response.json()
                body = issue_data.get('body', '')
                if body:
                    closing_issues.append(body)
            except httpx.HTTPError as exc:
                logger.warning(f'Failed to fetch issue {issue_number}: {exc}')

        return closing_issues