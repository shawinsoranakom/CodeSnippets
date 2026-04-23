def duplicate_and_parse(cls, kb, docs, tenant_id, src, auto_parse=True):
        from api.db.services.file_service import FileService
        if not docs:
            return None

        class FileObj(BaseModel):
            id: str
            filename: str
            blob: bytes

            def read(self) -> bytes:
                return self.blob

        errs = []
        files = [FileObj(id=d["id"], filename=d["semantic_identifier"]+(f"{d['extension']}" if d["semantic_identifier"][::-1].find(d['extension'][::-1])<0 else ""), blob=d["blob"]) for d in docs]
        doc_ids = []
        err, doc_blob_pairs = FileService.upload_document(kb, files, tenant_id, src)
        errs.extend(err)

        # Create a mapping from filename to metadata for later use
        metadata_map = {}
        for d in docs:
            if d.get("metadata"):
                filename = d["semantic_identifier"]+(f"{d['extension']}" if d["semantic_identifier"][::-1].find(d['extension'][::-1])<0 else "")
                metadata_map[filename] = d["metadata"]

        kb_table_num_map = {}
        for doc, _ in doc_blob_pairs:
            doc_ids.append(doc["id"])

            # Set metadata if available for this document
            if doc["name"] in metadata_map:
                DocMetadataService.update_document_metadata(doc["id"], metadata_map[doc["name"]])

            if not auto_parse or auto_parse == "0":
                continue
            DocumentService.run(tenant_id, doc, kb_table_num_map)

        return errs, doc_ids