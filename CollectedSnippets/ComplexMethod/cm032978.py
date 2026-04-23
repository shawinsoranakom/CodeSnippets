def _load_entries(
        self,
        start: SecondsSinceUnixEpoch | None = None,
        end: SecondsSinceUnixEpoch | None = None,
    ) -> GenerateDocumentsOutput:
        feed = self._read_feed(require_entries=False)
        batch: list[Document] = []

        for entry in feed.entries:
            updated_at = self._resolve_entry_time(entry)
            ts = updated_at.timestamp()

            if start is not None and ts <= start:
                continue
            if end is not None and ts > end:
                continue

            batch.append(self._build_document(entry, updated_at))

            if len(batch) >= self.batch_size:
                yield batch
                batch = []

        if batch:
            yield batch