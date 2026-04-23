async def _generate(self, task: dict):
        connector_kwargs = {
            "jira_base_url": self.conf["base_url"],
            "project_key": self.conf.get("project_key"),
            "jql_query": self.conf.get("jql_query"),
            "batch_size": self.conf.get("batch_size", INDEX_BATCH_SIZE),
            "include_comments": self.conf.get("include_comments", True),
            "include_attachments": self.conf.get("include_attachments", False),
            "labels_to_skip": self._normalize_list(self.conf.get("labels_to_skip")),
            "comment_email_blacklist": self._normalize_list(self.conf.get("comment_email_blacklist")),
            "scoped_token": self.conf.get("scoped_token", False),
            "attachment_size_limit": self.conf.get("attachment_size_limit"),
            "timezone_offset": self.conf.get("timezone_offset"),
            "time_buffer_seconds": self.conf.get("time_buffer_seconds"),
        }

        self.connector = JiraConnector(**connector_kwargs)

        credentials = self.conf.get("credentials")
        if not credentials:
            raise ValueError("Jira connector is missing credentials.")

        self.connector.load_credentials(credentials)
        self.connector.validate_connector_settings()

        if task["reindex"] == "1" or not task["poll_range_start"]:
            start_time = 0.0
            _begin_info = "totally"
        else:
            start_time = task["poll_range_start"].timestamp()
            _begin_info = f"from {task['poll_range_start']}"

        end_time = datetime.now(timezone.utc).timestamp()

        raw_batch_size = self.conf.get("sync_batch_size") or self.conf.get("batch_size") or INDEX_BATCH_SIZE
        try:
            batch_size = int(raw_batch_size)
        except (TypeError, ValueError):
            batch_size = INDEX_BATCH_SIZE
        if batch_size <= 0:
            batch_size = INDEX_BATCH_SIZE

        def document_batches():
            checkpoint = self.connector.build_dummy_checkpoint()
            pending_docs = []
            iterations = 0
            iteration_limit = 100_000

            while checkpoint.has_more:
                wrapper = CheckpointOutputWrapper()
                generator = wrapper(
                    self.connector.load_from_checkpoint(
                        start_time,
                        end_time,
                        checkpoint,
                    )
                )
                for document, failure, next_checkpoint in generator:
                    if failure is not None:
                        logging.warning(
                            f"[Jira] Jira connector failure: {getattr(failure, 'failure_message', failure)}"
                        )
                        continue
                    if document is not None:
                        pending_docs.append(document)
                        if len(pending_docs) >= batch_size:
                            yield pending_docs
                            pending_docs = []
                    if next_checkpoint is not None:
                        checkpoint = next_checkpoint

                iterations += 1
                if iterations > iteration_limit:
                    logging.error(f"[Jira] Task {task.get('id')} exceeded iteration limit ({iteration_limit}).")
                    raise RuntimeError("Too many iterations while loading Jira documents.")

            if pending_docs:
                yield pending_docs

        self.log_connection(
            "Jira",
            connector_kwargs["jira_base_url"],
            task,
            (
                f"sync_batch_size={batch_size}, "
                f"overlap_buffer_s={getattr(self.connector, 'time_buffer_seconds', connector_kwargs.get('time_buffer_seconds'))}"
            ),
        )
        return document_batches()