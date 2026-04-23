def _perform_jql_search_v3(
        self,
        *,
        jql: str,
        max_results: int,
        all_issue_ids: list[list[str]],
        fields: str | None = None,
        checkpoint_callback: Callable[[Iterable[list[str]], str | None], None] | None = None,
        next_page_token: str | None = None,
        ids_done: bool = False,
    ) -> Iterable[Issue]:
        assert self.jira_client, "Jira client not initialized."

        if not ids_done:
            new_ids, page_token = self._enhanced_search_ids(jql, next_page_token)
            if checkpoint_callback is not None and new_ids:
                checkpoint_callback(
                    self._chunk_issue_ids(new_ids, max_results),
                    page_token,
                )
            elif checkpoint_callback is not None:
                checkpoint_callback([], page_token)

        if all_issue_ids:
            issue_ids = all_issue_ids.pop()
            if issue_ids:
                yield from self._bulk_fetch_issues(issue_ids, fields)