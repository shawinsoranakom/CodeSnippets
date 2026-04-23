def _retrieve_articles(
        self,
        start: SecondsSinceUnixEpoch | None,
        end: SecondsSinceUnixEpoch | None,
        checkpoint: ZendeskConnectorCheckpoint,
    ) -> CheckpointOutput[ZendeskConnectorCheckpoint]:
        checkpoint = copy.deepcopy(checkpoint)
        # This one is built on the fly as there may be more many more authors than tags
        author_map: dict[str, BasicExpertInfo] = checkpoint.cached_author_map or {}
        after_cursor = checkpoint.after_cursor_articles
        doc_batch: list[Document] = []

        response = _get_article_page(
            self.client,
            start_time=int(start) if start else None,
            after_cursor=after_cursor,
        )
        articles = response.data
        has_more = response.has_more
        after_cursor = response.meta.get("after_cursor")
        for article in articles:
            if (
                article.get("body") is None
                or article.get("draft")
                or any(
                    label in ZENDESK_CONNECTOR_SKIP_ARTICLE_LABELS
                    for label in article.get("label_names", [])
                )
            ):
                continue

            try:
                new_author_map, document = _article_to_document(
                    article, self.content_tags, author_map, self.client
                )
            except Exception as e:
                logging.error(f"Error processing article {article['id']}: {e}")
                yield ConnectorFailure(
                    failed_document=DocumentFailure(
                        document_id=f"{article.get('id')}",
                        document_link=article.get("html_url", ""),
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

        # Sometimes no documents are retrieved, but the cursor
        # is still updated so the connector makes progress.
        yield from doc_batch
        checkpoint.after_cursor_articles = after_cursor

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