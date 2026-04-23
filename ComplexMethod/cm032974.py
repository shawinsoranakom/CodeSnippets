def retrieve_all_slim_docs_perm_sync(
        self,
        start: SecondsSinceUnixEpoch | None = None,
        end: SecondsSinceUnixEpoch | None = None,
        callback: IndexingHeartbeatInterface | None = None,
    ) -> GenerateSlimDocumentOutput:
        slim_doc_batch: list[SlimDocument] = []
        if self.content_type == "articles":
            articles = _get_articles(
                self.client, start_time=int(start) if start else None
            )
            for article in articles:
                slim_doc_batch.append(
                    SlimDocument(
                        id=f"article:{article['id']}",
                    )
                )
                if len(slim_doc_batch) >= _SLIM_BATCH_SIZE:
                    yield slim_doc_batch
                    slim_doc_batch = []
        elif self.content_type == "tickets":
            tickets = _get_tickets(
                self.client, start_time=int(start) if start else None
            )
            for ticket in tickets:
                slim_doc_batch.append(
                    SlimDocument(
                        id=f"zendesk_ticket_{ticket['id']}",
                    )
                )
                if len(slim_doc_batch) >= _SLIM_BATCH_SIZE:
                    yield slim_doc_batch
                    slim_doc_batch = []
        else:
            raise ValueError(f"Unsupported content_type: {self.content_type}")
        if slim_doc_batch:
            yield slim_doc_batch