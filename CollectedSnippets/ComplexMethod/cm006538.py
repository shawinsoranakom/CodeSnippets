def delete_storage(kb_path: Path, kb_name: str) -> bool:
        """Teardown ChromaDB connections and delete KB directory with retry logic.

        Handles ChromaDB SQLite file locks that can prevent deletion, particularly
        on Windows where mandatory file locks block deletion of open files.
        Uses retry with exponential backoff and rename-as-fallback strategy.

        Returns:
            True if deletion succeeded (or path already gone), False otherwise.
        """
        if not kb_path.exists():
            return True

        # Teardown ChromaDB collection to release handles
        try:
            has_data = any((kb_path / m).exists() for m in ["chroma", "chroma.sqlite3", "index"])
            if has_data:
                client = KBStorageHelper.get_fresh_chroma_client(kb_path)
                chroma = Chroma(client=client, collection_name=kb_name)
                with contextlib.suppress(Exception):
                    chroma.delete_collection()
                chroma = None
                client = None
        except (OSError, ValueError, TypeError, chromadb.errors.ChromaError) as e:
            logger.debug("Collection teardown failed for %s: %s", kb_path.name, e)

        gc.collect()

        for attempt in range(MAX_DELETE_RETRIES):
            try:
                if attempt > 0:
                    time.sleep(DELETE_BACKOFF_SECONDS * (2**attempt))

                _remove_sqlite_lock_files(kb_path)
                _truncate_sqlite_files(kb_path)
                gc.collect()

                shutil.rmtree(kb_path, ignore_errors=False)

                if not kb_path.exists():
                    logger.info("Deleted knowledge base %s on attempt %d", kb_name, attempt + 1)
                    return True

            except OSError as e:
                if attempt < MAX_DELETE_RETRIES - 1:
                    logger.debug("KB deletion attempt %d failed for %s: %s", attempt + 1, kb_name, e)
                else:
                    logger.warning(
                        "KB deletion failed for %s after %d attempts: %s",
                        kb_name,
                        MAX_DELETE_RETRIES,
                        e,
                    )

        # Last resort: rename for deferred cleanup
        if kb_path.exists():
            try:
                deferred = kb_path.with_name(f".deleted_{kb_name}_{int(time.time())}")
                kb_path.rename(deferred)
            except OSError as e:
                logger.warning("Deferred rename failed for %s: %s", kb_name, e)
            else:
                logger.info("Renamed %s for deferred cleanup", kb_name)
                return True

        return False