async def get_missing_items(self, batch_size: int) -> list[ContentItem]:
        """Fetch documentation sections without embeddings.

        Chunks each document by markdown headings and creates embeddings for each section.
        Content IDs use the format: 'path/to/doc.md::section_index'
        """
        docs_root = self._get_docs_root()

        if not docs_root.exists():
            logger.warning(f"Documentation root not found: {docs_root}")
            return []

        # Find all .md and .mdx files
        all_docs = list(docs_root.rglob("*.md")) + list(docs_root.rglob("*.mdx"))

        if not all_docs:
            return []

        # Build list of all sections from all documents
        all_sections: list[tuple[str, Path, MarkdownSection]] = []
        for doc_file in all_docs:
            doc_path = str(doc_file.relative_to(docs_root))
            sections = self._chunk_markdown_by_headings(doc_file)
            for section in sections:
                all_sections.append((doc_path, doc_file, section))

        if not all_sections:
            return []

        # Generate content IDs for all sections
        section_content_ids = [
            self._make_section_content_id(doc_path, section.index)
            for doc_path, _, section in all_sections
        ]

        # Check which ones have embeddings
        placeholders = ",".join([f"${i+1}" for i in range(len(section_content_ids))])
        existing_result = await query_raw_with_schema(
            f"""
            SELECT "contentId"
            FROM {{schema_prefix}}"UnifiedContentEmbedding"
            WHERE "contentType" = 'DOCUMENTATION'::{{schema_prefix}}"ContentType"
            AND "contentId" = ANY(ARRAY[{placeholders}])
            """,
            *section_content_ids,
        )

        existing_ids = {row["contentId"] for row in existing_result}

        # Filter to missing sections
        missing_sections = [
            (doc_path, doc_file, section, content_id)
            for (doc_path, doc_file, section), content_id in zip(
                all_sections, section_content_ids
            )
            if content_id not in existing_ids
        ]

        # Convert to ContentItem (up to batch_size)
        items = []
        for doc_path, doc_file, section, content_id in missing_sections[:batch_size]:
            try:
                # Get document title for context
                doc_title = self._extract_doc_title(doc_file)

                # Build searchable text with context
                # Include doc title and section title for better search relevance
                searchable_text = f"{doc_title} - {section.title}\n\n{section.content}"

                items.append(
                    ContentItem(
                        content_id=content_id,
                        content_type=ContentType.DOCUMENTATION,
                        searchable_text=searchable_text,
                        metadata={
                            "doc_title": doc_title,
                            "section_title": section.title,
                            "section_index": section.index,
                            "heading_level": section.level,
                            "path": doc_path,
                        },
                        user_id=None,  # Documentation is public
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to process section {content_id}: {e}")
                continue

        return items