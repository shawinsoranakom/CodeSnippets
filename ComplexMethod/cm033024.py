def _read_pages(self, pages: list[NotionPage], start: SecondsSinceUnixEpoch | None = None, end: SecondsSinceUnixEpoch | None = None) -> Generator[Document, None, None]:
        """Reads pages for rich text content and generates Documents."""
        all_child_page_ids: list[str] = []

        for page in pages:
            if isinstance(page, dict):
                page = NotionPage(**page)
            if page.id in self.indexed_pages:
                logging.debug(f"[Notion]: Already indexed page with ID {page.id}. Skipping.")
                continue

            if start is not None and end is not None:
                page_ts = datetime_from_string(page.last_edited_time).timestamp()
                if not (page_ts > start and page_ts <= end):
                    logging.debug(f"[Notion]: Skipping page {page.id} outside polling window.")
                    continue

            logging.info(f"[Notion]: Reading page with ID {page.id}, with url {page.url}")
            page_path = self._build_page_path(page)
            page_blocks, child_page_ids, attachment_docs = self._read_blocks(page.id, page.last_edited_time, page_path)
            all_child_page_ids.extend(child_page_ids)
            self.indexed_pages.add(page.id)

            raw_page_title = self._read_page_title(page)
            page_title = raw_page_title or f"Untitled Page with ID {page.id}"

            # Append the page id to help disambiguate duplicate names
            base_identifier = page_path or page_title
            semantic_identifier = f"{base_identifier}_{page.id}" if base_identifier else page.id

            if not page_blocks:
                if not raw_page_title:
                    logging.warning(f"[Notion]: No blocks OR title found for page with ID {page.id}. Skipping.")
                    continue

                text = page_title
                if page.properties:
                    text += "\n\n" + "\n".join([f"{key}: {value}" for key, value in page.properties.items()])
                sections = [TextSection(link=page.url, text=text)]
            else:
                sections = [
                    TextSection(
                        link=f"{page.url}#{block.id.replace('-', '')}",
                        text=block.prefix + block.text,
                    )
                    for block in page_blocks
                ]

            joined_text = "\n".join(sec.text for sec in sections)
            blob = joined_text.encode("utf-8")
            yield Document(
                id=page.id, blob=blob, source=DocumentSource.NOTION, semantic_identifier=semantic_identifier, extension=".txt", size_bytes=len(blob), doc_updated_at=datetime_from_string(page.last_edited_time)
            )

            for attachment_doc in attachment_docs:
                yield attachment_doc

        if self.recursive_index_enabled and all_child_page_ids:
            for child_page_batch_ids in batch_generator(all_child_page_ids, INDEX_BATCH_SIZE):
                child_page_batch = [self._fetch_page(page_id) for page_id in child_page_batch_ids if page_id not in self.indexed_pages]
                yield from self._read_pages(child_page_batch, start, end)