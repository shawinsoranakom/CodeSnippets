def retrieve_slim_document(
        self,
        start: SecondsSinceUnixEpoch | None = None,
        end: SecondsSinceUnixEpoch | None = None,
        callback: Any = None,
    ) -> GenerateSlimDocumentOutput:
        start_value = 0.0 if start is None else start
        end_value = (
            datetime.now(timezone.utc).timestamp() if end is None else end
        )
        checkpoint = self.build_dummy_checkpoint()
        slim_batch: list[SlimDocument] = []

        while checkpoint.has_more:
            wrapper = CheckpointOutputWrapper[GithubConnectorCheckpoint]()
            for document, failure, next_checkpoint in wrapper(
                self.load_from_checkpoint(start_value, end_value, checkpoint)
            ):
                if failure is not None:
                    logging.warning(
                        "GitHub connector failure during slim retrieval: %s",
                        getattr(failure, "failure_message", failure),
                    )
                    continue

                if document is not None:
                    slim_batch.append(SlimDocument(id=document.id))
                    if len(slim_batch) >= SLIM_BATCH_SIZE:
                        yield slim_batch
                        slim_batch = []
                        if callback:
                            callback.progress("github_slim_document", 1)

                if next_checkpoint is not None:
                    checkpoint = next_checkpoint

        if slim_batch:
            yield slim_batch