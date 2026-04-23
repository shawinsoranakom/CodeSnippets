def _fetch_page_attachments(
        self,
        page: dict[str, Any],
        start: SecondsSinceUnixEpoch | None = None,
        end: SecondsSinceUnixEpoch | None = None,
    ) -> tuple[list[Document], list[ConnectorFailure]]:
        """
        Inline attachments are added directly to the document as text or image sections by
        this function. The returned documents/connectorfailures are for non-inline attachments
        and those at the end of the page.
        """
        attachment_query = self._construct_attachment_query(page["id"], start, end)
        attachment_failures: list[ConnectorFailure] = []
        attachment_docs: list[Document] = []
        page_url = ""

        for attachment in self.confluence_client.paginated_cql_retrieval(
            cql=attachment_query,
            expand=",".join(_ATTACHMENT_EXPANSION_FIELDS),
        ):
            media_type: str = attachment.get("metadata", {}).get("mediaType", "")
            # TODO(rkuo): this check is partially redundant with validate_attachment_filetype
            # and checks in convert_attachment_to_content/process_attachment
            # but doing the check here avoids an unnecessary download. Due for refactoring.
            if not self.allow_images:
                if media_type.startswith("image/"):
                    logging.info(
                        f"Skipping attachment because allow images is False: {attachment['title']}"
                    )
                    continue

            if not validate_attachment_filetype(
                attachment,
            ):
                logging.info(
                    f"Skipping attachment because it is not an accepted file type: {attachment['title']}"
                )
                continue


            logging.info(
                f"Processing attachment: {attachment['title']} attached to page {page['title']}"
            )
            # Attachment document id: use the download URL for stable identity
            try:
                object_url = build_confluence_document_id(
                    self.wiki_base, attachment["_links"]["download"], self.is_cloud
                )
            except Exception as e:
                logging.warning(
                    f"Invalid attachment url for id {attachment['id']}, skipping"
                )
                logging.debug(f"Error building attachment url: {e}")
                continue
            try:
                response = convert_attachment_to_content(
                    confluence_client=self.confluence_client,
                    attachment=attachment,
                    page_id=page["id"],
                    allow_images=self.allow_images,
                )
                if response is None:
                    continue

                file_storage_name, file_blob = response

                if not file_blob:
                    logging.info("Skipping attachment because it is no blob fetched")
                    continue

                # Build attachment-specific metadata
                attachment_metadata: dict[str, str | list[str]] = {}
                if "space" in attachment:
                    attachment_metadata["space"] = attachment["space"].get("name", "")
                labels: list[str] = []
                if "metadata" in attachment and "labels" in attachment["metadata"]:
                    for label in attachment["metadata"]["labels"].get("results", []):
                        labels.append(label.get("name", ""))
                if labels:
                    attachment_metadata["labels"] = labels
                page_url = page_url or build_confluence_document_id(
                    self.wiki_base, page["_links"]["webui"], self.is_cloud
                )
                attachment_metadata["parent_page_id"] = page_url
                attachment_id = build_confluence_document_id(
                    self.wiki_base, attachment["_links"]["webui"], self.is_cloud
                )

                # Build semantic identifier with space and page context
                attachment_title = attachment.get("title", object_url)
                space_name = page.get("space", {}).get("name", "")
                page_title = page.get("title", "")

                # Create hierarchical name: Space / Page / Attachment
                attachment_path_parts = []
                if space_name:
                    attachment_path_parts.append(space_name)
                if page_title:
                    attachment_path_parts.append(page_title)
                attachment_path_parts.append(attachment_title)

                full_attachment_path = " / ".join(attachment_path_parts) if len(attachment_path_parts) > 1 else attachment_title

                # Track attachment names for duplicate detection
                if attachment_title not in self._document_name_counts:
                    self._document_name_counts[attachment_title] = 0
                    self._document_name_paths[attachment_title] = []
                self._document_name_counts[attachment_title] += 1
                self._document_name_paths[attachment_title].append(full_attachment_path)

                # Use simple name if no duplicates, otherwise use full path
                if self._document_name_counts[attachment_title] == 1:
                    attachment_semantic_identifier = attachment_title
                else:
                    attachment_semantic_identifier = full_attachment_path

                primary_owners: list[BasicExpertInfo] | None = None
                if "version" in attachment and "by" in attachment["version"]:
                    author = attachment["version"]["by"]
                    display_name = author.get("displayName", "Unknown")
                    email = author.get("email", "unknown@domain.invalid")
                    primary_owners = [
                        BasicExpertInfo(display_name=display_name, email=email)
                    ]

                extension = Path(attachment.get("title", "")).suffix or ".unknown"


                attachment_doc = Document(
                    id=attachment_id,
                    # sections=sections,
                    source=DocumentSource.CONFLUENCE,
                    semantic_identifier=attachment_semantic_identifier,
                    extension=extension,
                    blob=file_blob,
                    size_bytes=len(file_blob),
                    metadata=attachment_metadata,
                    doc_updated_at=(
                        datetime_from_string(attachment["version"]["when"])
                        if attachment.get("version")
                        and attachment["version"].get("when")
                        else None
                    ),
                    primary_owners=primary_owners,
                )
                if self._is_newer_than_start(attachment_doc.doc_updated_at, start):
                    attachment_docs.append(attachment_doc)
            except Exception as e:
                logging.error(
                    f"Failed to extract/summarize attachment {attachment['title']}",
                    exc_info=e,
                )
                if is_atlassian_date_error(e):
                    # propagate error to be caught and retried
                    raise
                attachment_failures.append(
                    ConnectorFailure(
                        failed_document=DocumentFailure(
                            document_id=object_url,
                            document_link=object_url,
                        ),
                        failure_message=f"Failed to extract/summarize attachment {attachment['title']} for doc {object_url}",
                        exception=e,
                    )
                )

        return attachment_docs, attachment_failures