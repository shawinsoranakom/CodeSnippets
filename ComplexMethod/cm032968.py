def _yield_seafile_documents(
        self, start: datetime, end: datetime,
    ) -> GenerateDocumentsOutput:
        libraries = self._resolve_libraries_to_scan()
        logger.info(
            "Processing %d library(ies) [scope=%s]",
            len(libraries), self.sync_scope.value,
        )

        all_files: list[tuple[str, dict, dict]] = []
        for lib in libraries:
            root = self._root_path_for_repo(lib["id"])
            logger.debug("Scanning %s starting at %s", lib["name"], root)
            try:
                files = self._list_files_recursive(
                    lib["id"], lib["name"], root, start, end,
                )
                all_files.extend(files)
            except Exception as e:
                logger.error("Error in library %s: %s", lib["name"], e)

        logger.info("Found %d file(s) matching criteria", len(all_files))

        batch: list[Document] = []
        for file_path, file_entry, library in all_files:
            file_name = file_entry.get("name", "")
            file_size = file_entry.get("size", 0)
            file_id = file_entry.get("id", "")
            repo_id = library["id"]
            repo_name = library["name"]

            modified = self._parse_mtime(file_entry.get("mtime"))

            if file_size > self.size_threshold:
                logger.warning("Skipping large file: %s (%d B)", file_path, file_size)
                continue

            try:
                download_link = self._get_file_download_link(repo_id, file_path)
                if not download_link:
                    continue

                resp = rl_requests.get(download_link, timeout=120)
                resp.raise_for_status()
                blob = resp.content
                if not blob:
                    continue

                batch.append(Document(
                    id=f"seafile:{repo_id}:{file_id}",
                    blob=blob,
                    source=DocumentSource.SEAFILE,
                    semantic_identifier=f"{repo_name}{file_path}",
                    extension=get_file_ext(file_name),
                    doc_updated_at=modified,          # <-- already parsed
                    size_bytes=len(blob),
                ))

                if len(batch) >= self.batch_size:
                    yield batch
                    batch = []

            except Exception as e:
                logger.error("Error downloading %s: %s", file_path, e)

        if batch:
            yield batch