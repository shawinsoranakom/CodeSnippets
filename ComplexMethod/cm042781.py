def _upload_file(self, files: list[str]) -> None:
        logger.debug("Loading count=%s files", len(files))
        paths = [Path(file) for file in files]

        # remove all existing Documents with name identical to a new file upload:
        file_names = [path.name for path in paths]
        doc_ids_to_delete = []
        for ingested_document in self._ingest_service.list_ingested():
            if (
                ingested_document.doc_metadata
                and ingested_document.doc_metadata["file_name"] in file_names
            ):
                doc_ids_to_delete.append(ingested_document.doc_id)
        if len(doc_ids_to_delete) > 0:
            logger.info(
                "Uploading file(s) which were already ingested: %s document(s) will be replaced.",
                len(doc_ids_to_delete),
            )
            for doc_id in doc_ids_to_delete:
                self._ingest_service.delete(doc_id)

        self._ingest_service.bulk_ingest([(str(path.name), path) for path in paths])