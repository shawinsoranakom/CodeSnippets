def get_metadata(kb_path: Path, *, fast: bool = False) -> dict:
        """Extract metadata from a knowledge base directory."""
        metadata_file = kb_path / "embedding_metadata.json"
        defaults = {
            "chunks": 0,
            "words": 0,
            "characters": 0,
            "avg_chunk_size": 0.0,
            "embedding_provider": "Unknown",
            "embedding_model": "Unknown",
            "id": str(uuid.uuid4()),
            "size": 0,
            "source_types": [],
            "chunk_size": None,
            "chunk_overlap": None,
            "separator": None,
        }

        metadata = {}
        if metadata_file.exists():
            try:
                metadata = json.loads(metadata_file.read_text())
            except (OSError, json.JSONDecodeError):
                logger.warning(f"Failed to parse metadata file for {kb_path.name}, resetting to defaults.")

        missing_keys = not all(k in metadata for k in defaults)
        has_unknowns = metadata.get("embedding_provider") == "Unknown" or metadata.get("embedding_model") == "Unknown"
        # Detect stale zero-chunk metadata: the file claims 0 chunks but
        # Chroma data exists on disk, meaning data was ingested without updating
        # the metrics (e.g. via the KnowledgeIngestionComponent before the fix).
        has_chroma_data = any((kb_path / m).exists() for m in ["chroma", "chroma.sqlite3", "index"])
        stale_chunks = metadata.get("chunks", 0) == 0 and has_chroma_data

        if fast and not missing_keys and not stale_chunks:
            return metadata

        backfill_needed = not metadata_file.exists() or missing_keys or (not fast and has_unknowns)

        if backfill_needed:
            for key, default_val in defaults.items():
                if key not in metadata or (key == "id" and not metadata[key]):
                    metadata[key] = default_val

            try:
                metadata["size"] = KBStorageHelper.get_directory_size(kb_path)
                if metadata.get("embedding_provider") == "Unknown":
                    metadata["embedding_provider"] = KBAnalysisHelper._detect_embedding_provider(kb_path)
                if metadata.get("embedding_model") == "Unknown":
                    metadata["embedding_model"] = KBAnalysisHelper._detect_embedding_model(kb_path)

                metadata_file.write_text(json.dumps(metadata, indent=2))
            except (OSError, ValueError, TypeError, json.JSONDecodeError) as e:
                logger.debug(f"Metadata backfill failed for {kb_path}: {e}")

        # Recount metrics from Chroma if metadata claims 0 chunks but data exists
        if stale_chunks:
            try:
                KBAnalysisHelper.update_text_metrics(kb_path, metadata)
                metadata["size"] = KBStorageHelper.get_directory_size(kb_path)
                metadata_file.write_text(json.dumps(metadata, indent=2))
            except (OSError, ValueError, TypeError, json.JSONDecodeError, chromadb.errors.ChromaError) as e:
                logger.debug(f"Stale metrics recount failed for {kb_path}: {e}")

        return metadata