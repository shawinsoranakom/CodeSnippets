def insert_document_metadata(cls, doc_id: str, meta_fields: Dict) -> bool:
        """
        Insert document metadata into ES/Infinity.

        Args:
            doc_id: Document ID
            meta_fields: Metadata dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get document with tenant_id (need to join with Knowledgebase)
            doc_query = Document.select(Document, Knowledgebase.tenant_id).join(
                Knowledgebase, on=(Knowledgebase.id == Document.kb_id)
            ).where(Document.id == doc_id)

            doc = doc_query.first()
            if not doc:
                logging.warning(f"Document {doc_id} not found for metadata insertion")
                return False

            # Extract document fields
            doc_obj = doc  # This is the Document object
            tenant_id = doc.knowledgebase.tenant_id  # Get tenant_id from joined Knowledgebase
            kb_id = doc_obj.kb_id

            # Prepare metadata document
            doc_meta = {
                "id": doc_obj.id,
                "kb_id": kb_id,
            }

            # Store metadata as JSON object in meta_fields column (same as MySQL structure)
            if meta_fields:
                # Post-process to split combined values by common delimiters
                meta_fields = cls._split_combined_values(meta_fields)
                doc_meta["meta_fields"] = meta_fields
            else:
                doc_meta["meta_fields"] = {}

            # Ensure index/table exists (per-tenant for both ES and Infinity)
            index_name = cls._get_doc_meta_index_name(tenant_id)

            # Check if table exists
            table_exists = settings.docStoreConn.index_exist(index_name, kb_id)
            logging.debug(f"Metadata table exists check: {index_name} -> {table_exists}")

            # Create index if it doesn't exist
            if not table_exists:
                logging.debug(f"Creating metadata table: {index_name}")
                # Both ES and Infinity now use per-tenant metadata tables
                result = settings.docStoreConn.create_doc_meta_idx(index_name)
                logging.debug(f"Table creation result: {result}")
                if result is False:
                    logging.error(f"Failed to create metadata table {index_name}")
                    return False
            else:
                logging.debug(f"Metadata table already exists: {index_name}")

            # Insert into ES/Infinity
            result = settings.docStoreConn.insert(
                [doc_meta],
                index_name,
                kb_id
            )

            if result:
                logging.error(f"Failed to insert metadata for document {doc_id}: {result}")
                return False
            # Force ES refresh to make metadata immediately available for search
            if not settings.DOC_ENGINE_INFINITY:
                try:
                    settings.docStoreConn.es.indices.refresh(index=index_name)
                    logging.debug(f"Refreshed metadata index: {index_name}")
                except Exception as e:
                    logging.warning(f"Failed to refresh metadata index {index_name}: {e}")

            logging.debug(f"Successfully inserted metadata for document {doc_id}")
            return True

        except Exception as e:
            logging.error(f"Error inserting metadata for document {doc_id}: {e}")
            return False