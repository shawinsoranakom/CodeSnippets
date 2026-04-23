def update_text_metrics(kb_path: Path, metadata: dict, chroma: Chroma | None = None) -> None:
        """Update text metrics (chunks, words, characters) for a knowledge base."""
        created_locally = chroma is None
        client = None
        try:
            if created_locally:
                client = KBStorageHelper.get_fresh_chroma_client(kb_path)
                chroma = Chroma(client=client, collection_name=kb_path.name)

            if chroma is None:
                return
            collection = chroma._collection  # noqa: SLF001
            metadata["chunks"] = collection.count()

            if metadata["chunks"] > 0:
                total_words = 0
                total_characters = 0
                # Use a robust batch size to avoid SQLite limits and memory pressure
                batch_size = 5000

                for offset in range(0, metadata["chunks"], batch_size):
                    results = collection.get(
                        include=["documents"],
                        limit=batch_size,
                        offset=offset,
                    )
                    if not results["documents"]:
                        break

                    # Chroma collections always return the text content within the 'documents' field
                    source_chunks = pd.DataFrame({"document": results["documents"]})
                    words, characters = KBAnalysisHelper._calculate_text_metrics(source_chunks, ["document"])
                    total_words += words
                    total_characters += characters

                metadata["words"] = total_words
                metadata["characters"] = total_characters
                metadata["avg_chunk_size"] = (
                    round(total_characters / metadata["chunks"], 1) if metadata["chunks"] > 0 else 0.0
                )
        except (OSError, ValueError, TypeError, json.JSONDecodeError, chromadb.errors.ChromaError) as e:
            logger.debug(f"Metrics update failed for {kb_path.name}: {e}")
        finally:
            if created_locally:
                client = None
                chroma = None
                KBStorageHelper.release_chroma_resources(kb_path)