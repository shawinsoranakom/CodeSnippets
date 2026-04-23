def update_document_metadata(cls, doc_id: str, meta_fields: Dict) -> bool:
        """
        Update document metadata in ES/Infinity.

        For Elasticsearch: Uses partial update to directly update the meta_fields field.
        For Infinity: Falls back to delete+insert (Infinity doesn't support partial updates well).

        Args:
            doc_id: Document ID
            meta_fields: Metadata dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get document with tenant_id
            doc_query = Document.select(Document, Knowledgebase.tenant_id).join(
                Knowledgebase, on=(Knowledgebase.id == Document.kb_id)
            ).where(Document.id == doc_id)

            doc = doc_query.first()
            if not doc:
                logging.warning(f"Document {doc_id} not found for metadata update")
                return False

            # Extract fields
            doc_obj = doc
            tenant_id = doc.knowledgebase.tenant_id
            kb_id = doc_obj.kb_id
            index_name = cls._get_doc_meta_index_name(tenant_id)

            # Post-process to split combined values
            processed_meta = cls._split_combined_values(meta_fields)

            logging.debug(f"[update_document_metadata] Updating doc_id: {doc_id}, kb_id: {kb_id}, meta_fields: {processed_meta}")

            # For Elasticsearch, use efficient partial update
            if not settings.DOC_ENGINE_INFINITY and not settings.DOC_ENGINE_OCEANBASE:
                # Check if index exists first
                index_exists = settings.docStoreConn.index_exist(index_name, "")
                if not index_exists:
                    # Index doesn't exist - create it and insert directly
                    logging.debug(f"[update_document_metadata] Index {index_name} does not exist, creating and inserting")
                    result = settings.docStoreConn.create_doc_meta_idx(index_name)
                    if result is False:
                        logging.error(f"Failed to create metadata index {index_name}")
                        return False
                    return cls.insert_document_metadata(doc_id, processed_meta)

                # Index exists - check if document exists
                try:
                    doc_exists = settings.docStoreConn.get(
                        index_name=index_name,
                        id=doc_id,
                        kb_id=kb_id
                    )
                    if doc_exists:
                        # Document exists - use partial update
                        settings.docStoreConn.es.update(
                            index=index_name,
                            id=doc_id,
                            refresh=True,
                            doc={"meta_fields": processed_meta}
                        )
                        logging.debug(f"Successfully updated metadata for document {doc_id} using ES partial update")
                        return True
                except Exception as e:
                    logging.debug(f"Document {doc_id} not found in index, will insert: {e}")

                # Document doesn't exist - insert new
                logging.debug(f"[update_document_metadata] Document {doc_id} not found, inserting new")
                return cls.insert_document_metadata(doc_id, processed_meta)

            # For Infinity or as fallback: use delete+insert
            logging.debug(f"[update_document_metadata] Using delete+insert method for doc_id: {doc_id}")
            cls.delete_document_metadata(doc_id, kb_id, tenant_id)
            return cls.insert_document_metadata(doc_id, processed_meta)

        except Exception as e:
            logging.error(f"Error updating metadata for document {doc_id}: {e}")
            return False