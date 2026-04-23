def _retrieve_all_slim_docs(
        self,
        start: SecondsSinceUnixEpoch | None = None,
        end: SecondsSinceUnixEpoch | None = None,
        callback: IndexingHeartbeatInterface | None = None,
        include_permissions: bool = True,
    ) -> GenerateSlimDocumentOutput:
        doc_metadata_list: list[SlimDocument] = []
        restrictions_expand = ",".join(_RESTRICTIONS_EXPANSION_FIELDS)

        space_level_access_info: dict[str, ExternalAccess] = {}
        if include_permissions:
            space_level_access_info = get_all_space_permissions(
                self.confluence_client, self.is_cloud
            )

        def get_external_access(
            doc_id: str, restrictions: dict[str, Any], ancestors: list[dict[str, Any]]
        ) -> ExternalAccess | None:
            return get_page_restrictions(
                self.confluence_client, doc_id, restrictions, ancestors
            ) or space_level_access_info.get(page_space_key)

        # Query pages
        page_query = self.base_cql_page_query + self.cql_label_filter
        for page in self.confluence_client.cql_paginate_all_expansions(
            cql=page_query,
            expand=restrictions_expand,
            limit=_SLIM_DOC_BATCH_SIZE,
        ):
            page_id = page["id"]
            page_restrictions = page.get("restrictions") or {}
            page_space_key = page.get("space", {}).get("key")
            page_ancestors = page.get("ancestors", [])

            page_id = build_confluence_document_id(
                self.wiki_base, page["_links"]["webui"], self.is_cloud
            )
            doc_metadata_list.append(
                SlimDocument(
                    id=page_id,
                    external_access=(
                        get_external_access(page_id, page_restrictions, page_ancestors)
                        if include_permissions
                        else None
                    ),
                )
            )

            # Query attachments for each page
            attachment_query = self._construct_attachment_query(page["id"])
            for attachment in self.confluence_client.cql_paginate_all_expansions(
                cql=attachment_query,
                expand=restrictions_expand,
                limit=_SLIM_DOC_BATCH_SIZE,
            ):
                # If you skip images, you'll skip them in the permission sync
                attachment["metadata"].get("mediaType", "")
                if not validate_attachment_filetype(
                    attachment,
                ):
                    continue

                attachment_restrictions = attachment.get("restrictions", {})
                if not attachment_restrictions:
                    attachment_restrictions = page_restrictions or {}

                attachment_space_key = attachment.get("space", {}).get("key")
                if not attachment_space_key:
                    attachment_space_key = page_space_key

                attachment_id = build_confluence_document_id(
                    self.wiki_base,
                    attachment["_links"]["webui"],
                    self.is_cloud,
                )
                doc_metadata_list.append(
                    SlimDocument(
                        id=attachment_id,
                        external_access=(
                            get_external_access(
                                attachment_id, attachment_restrictions, []
                            )
                            if include_permissions
                            else None
                        ),
                    )
                )

            if len(doc_metadata_list) > _SLIM_DOC_BATCH_SIZE:
                yield doc_metadata_list[:_SLIM_DOC_BATCH_SIZE]
                doc_metadata_list = doc_metadata_list[_SLIM_DOC_BATCH_SIZE:]

                if callback and callback.should_stop():
                    raise RuntimeError(
                        "retrieve_all_slim_docs_perm_sync: Stop signal detected"
                    )
                if callback:
                    callback.progress("retrieve_all_slim_docs_perm_sync", 1)

        yield doc_metadata_list