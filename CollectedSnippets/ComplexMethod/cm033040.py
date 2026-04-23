def _load_from_checkpoint_internal(
        self,
        jql: str,
        checkpoint: JiraCheckpoint,
        start_filter: SecondsSinceUnixEpoch | None = None,
    ) -> Generator[Document | ConnectorFailure, None, JiraCheckpoint]:
        assert self.jira_client, "load_credentials must be called before loading issues."

        page_size = self._full_page_size()
        new_checkpoint = copy.deepcopy(checkpoint)
        starting_offset = new_checkpoint.start_at or 0
        current_offset = starting_offset
        checkpoint_callback = self._make_checkpoint_callback(new_checkpoint)

        issue_iter = self._perform_jql_search(
            jql=jql,
            start=current_offset,
            max_results=page_size,
            fields=self._fields_param,
            all_issue_ids=new_checkpoint.all_issue_ids,
            checkpoint_callback=checkpoint_callback,
            next_page_token=new_checkpoint.cursor,
            ids_done=new_checkpoint.ids_done,
        )

        start_cutoff = float(start_filter) if start_filter is not None else None

        for issue in issue_iter:
            current_offset += 1
            issue_key = getattr(issue, "key", "unknown")
            if should_skip_issue(issue, self.labels_to_skip):
                continue

            issue_updated = parse_jira_datetime(issue.raw.get("fields", {}).get("updated"))
            if start_cutoff is not None and issue_updated is not None and issue_updated.timestamp() <= start_cutoff:
                # Jira JQL only supports minute precision, so we discard already-processed
                # issues here based on the original second-level cutoff.
                continue

            try:
                document = self._issue_to_document(issue)
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception(f"[Jira] Failed to convert Jira issue {issue_key}: {exc}")
                yield ConnectorFailure(
                    failure_message=f"Failed to convert Jira issue {issue_key}: {exc}",
                    failed_document=DocumentFailure(
                        document_id=issue_key,
                        document_link=build_issue_url(self.jira_base_url, issue_key),
                    ),
                    exception=exc,
                )
                continue

            if document is not None:
                yield document
                if self.include_attachments:
                    for attachment_document in self._attachment_documents(issue):
                        if attachment_document is not None:
                            yield attachment_document

        self._update_checkpoint_for_next_run(
            checkpoint=new_checkpoint,
            current_offset=current_offset,
            starting_offset=starting_offset,
            page_size=page_size,
        )
        new_checkpoint.start_at = current_offset
        return new_checkpoint