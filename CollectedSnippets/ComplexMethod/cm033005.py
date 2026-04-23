def _convert_page_to_document(
        self, page: dict[str, Any]
    ) -> Document | ConnectorFailure:
        """
        Converts a Confluence page to a Document object.
        Includes the page content, comments, and attachments.
        """
        page_id = page_url = ""
        try:
            # Extract basic page information
            page_id = page["id"]
            page_title = page["title"]
            logging.info(f"Converting page {page_title} to document")
            page_url = build_confluence_document_id(
                self.wiki_base, page["_links"]["webui"], self.is_cloud
            )

            # Build hierarchical path for semantic identifier
            space_name = page.get("space", {}).get("name", "")

            # Build path from ancestors
            path_parts = []
            if space_name:
                path_parts.append(space_name)

            # Add ancestor pages to path if available
            if "ancestors" in page and page["ancestors"]:
                for ancestor in page["ancestors"]:
                    ancestor_title = ancestor.get("title", "")
                    if ancestor_title:
                        path_parts.append(ancestor_title)

            # Add current page title
            path_parts.append(page_title)

            # Track page names for duplicate detection
            full_path = " / ".join(path_parts) if len(path_parts) > 1 else page_title

            # Count occurrences of this page title
            if page_title not in self._document_name_counts:
                self._document_name_counts[page_title] = 0
                self._document_name_paths[page_title] = []
            self._document_name_counts[page_title] += 1
            self._document_name_paths[page_title].append(full_path)

            # Use simple name if no duplicates, otherwise use full path
            if self._document_name_counts[page_title] == 1:
                semantic_identifier = page_title
            else:
                semantic_identifier = full_path

            # Get the page content
            page_content = extract_text_from_confluence_html(
                self.confluence_client, page, self._fetched_titles
            )

            # Create the main section for the page content
            sections: list[TextSection | ImageSection] = [
                TextSection(text=page_content, link=page_url)
            ]

            # Process comments if available
            comment_text = self._get_comment_string_for_page_id(page_id)
            if comment_text:
                sections.append(
                    TextSection(text=comment_text, link=f"{page_url}#comments")
                )
            # Note: attachments are no longer merged into the page document.
            # They are indexed as separate documents downstream.

            # Extract metadata
            metadata = {}
            if "space" in page:
                metadata["space"] = page["space"].get("name", "")

            # Extract labels
            labels = []
            if "metadata" in page and "labels" in page["metadata"]:
                for label in page["metadata"]["labels"].get("results", []):
                    labels.append(label.get("name", ""))
            if labels:
                metadata["labels"] = labels

            # Extract owners
            primary_owners = []
            if "version" in page and "by" in page["version"]:
                author = page["version"]["by"]
                display_name = author.get("displayName", "Unknown")
                email = author.get("email", "unknown@domain.invalid")
                primary_owners.append(
                    BasicExpertInfo(display_name=display_name, email=email)
                )

            # Create the document
            return Document(
                id=page_url,
                source=DocumentSource.CONFLUENCE,
                semantic_identifier=semantic_identifier,
                extension=".txt",  # Confluence pages are HTML
                blob=page_content.encode("utf-8"),  # Encode page content as bytes
                doc_updated_at=datetime_from_string(page["version"]["when"]),
                size_bytes=len(page_content.encode("utf-8")),  # Calculate size in bytes
                primary_owners=primary_owners if primary_owners else None,
                metadata=metadata if metadata else None,
            )
        except Exception as e:
            logging.error(f"Error converting page {page.get('id', 'unknown')}: {e}")
            if is_atlassian_date_error(e):  # propagate error to be caught and retried
                raise
            return ConnectorFailure(
                failed_document=DocumentFailure(
                    document_id=page_id,
                    document_link=page_url,
                ),
                failure_message=f"Error converting page {page.get('id', 'unknown')}: {e}",
                exception=e,
            )