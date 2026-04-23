def _retrieve_tickets(
        self,
        start: SecondsSinceUnixEpoch | None,
        end: SecondsSinceUnixEpoch | None,
        checkpoint: ZendeskConnectorCheckpoint,
    ) -> CheckpointOutput[ZendeskConnectorCheckpoint]:
        checkpoint = copy.deepcopy(checkpoint)
        if self.client is None:
            raise ZendeskCredentialsNotSetUpError()

        author_map: dict[str, BasicExpertInfo] = checkpoint.cached_author_map or {}

        doc_batch: list[Document] = []
        next_start_time = int(checkpoint.next_start_time_tickets or start or 0)
        ticket_response = _get_tickets_page(self.client, start_time=next_start_time)

        tickets = ticket_response.data
        has_more = ticket_response.has_more
        next_start_time = ticket_response.meta["end_time"]
        for ticket in tickets:
            if ticket.get("status") == "deleted":
                continue

            try:
                new_author_map, document = _ticket_to_document(
                    ticket=ticket,
                    author_map=author_map,
                    client=self.client,
                )
            except Exception as e:
                logging.error(f"Error processing ticket {ticket['id']}: {e}")
                yield ConnectorFailure(
                    failed_document=DocumentFailure(
                        document_id=f"{ticket.get('id')}",
                        document_link=ticket.get("url", ""),
                    ),
                    failure_message=str(e),
                    exception=e,
                )
                continue

            if new_author_map:
                author_map.update(new_author_map)

            updated_at = document.doc_updated_at
            updated_ts = updated_at.timestamp() if updated_at else None

            if updated_ts is not None:
                if start is not None and updated_ts <= start:
                    continue
                if end is not None and updated_ts > end:
                    continue

            doc_batch.append(document)

        if not has_more:
            yield from doc_batch
            checkpoint.has_more = False
            return checkpoint

        yield from doc_batch
        checkpoint.next_start_time_tickets = next_start_time
        last_doc_updated_at = doc_batch[-1].doc_updated_at if doc_batch else None
        checkpoint.has_more = bool(
            end is None
            or last_doc_updated_at is None
            or last_doc_updated_at.timestamp() <= end
        )
        checkpoint.cached_author_map = (
            author_map if len(author_map) <= MAX_AUTHOR_MAP_SIZE else None
        )
        return checkpoint