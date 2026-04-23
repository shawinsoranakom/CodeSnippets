def retrieve_all_slim_docs_perm_sync(
        self,
        start: SecondsSinceUnixEpoch | None = None,
        end: SecondsSinceUnixEpoch | None = None,
        callback: Any = None,  # noqa: ARG002 - maintained for interface compatibility
    ) -> Generator[list[SlimDocument], None, None]:
        """Return lightweight references to Jira issues (used for permission syncing)."""
        if not self.jira_client:
            raise ConnectorMissingCredentialError("Jira")

        start_ts = start if start is not None else 0
        end_ts = end if end is not None else datetime.now(timezone.utc).timestamp()
        jql = self._build_jql(start_ts, end_ts)

        checkpoint = self.build_dummy_checkpoint()
        checkpoint_callback = self._make_checkpoint_callback(checkpoint)
        prev_offset = 0
        current_offset = 0
        slim_batch: list[SlimDocument] = []

        while checkpoint.has_more:
            for issue in self._perform_jql_search(
                jql=jql,
                start=current_offset,
                max_results=_JIRA_SLIM_PAGE_SIZE,
                fields=self._slim_fields,
                all_issue_ids=checkpoint.all_issue_ids,
                checkpoint_callback=checkpoint_callback,
                next_page_token=checkpoint.cursor,
                ids_done=checkpoint.ids_done,
            ):
                current_offset += 1
                if should_skip_issue(issue, self.labels_to_skip):
                    continue

                doc_id = build_issue_url(self.jira_base_url, issue.key)
                slim_batch.append(SlimDocument(id=doc_id))

                if len(slim_batch) >= _JIRA_SLIM_PAGE_SIZE:
                    yield slim_batch
                    slim_batch = []

            self._update_checkpoint_for_next_run(
                checkpoint=checkpoint,
                current_offset=current_offset,
                starting_offset=prev_offset,
                page_size=_JIRA_SLIM_PAGE_SIZE,
            )
            prev_offset = current_offset

        if slim_batch:
            yield slim_batch