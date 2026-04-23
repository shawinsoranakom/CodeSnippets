async def perform_ingestion(
        kb_name: str,
        kb_path: Path,
        files_data: list[tuple[str, bytes]],
        chunk_size: int,
        chunk_overlap: int,
        separator: str,
        source_name: str,
        current_user: CurrentActiveUser,
        embedding_provider: str,
        embedding_model: str,
        task_job_id: uuid.UUID,
        job_service: JobService,
    ) -> dict[str, object]:
        """Orchestrate the ingestion of files into a knowledge base."""
        try:
            processed_files = []
            total_chunks_created = 0

            splitter_kwargs: dict = {"chunk_size": chunk_size, "chunk_overlap": chunk_overlap}
            if separator:
                resolved_separator = separator.replace("\\n", "\n")
                splitter_kwargs["separators"] = [resolved_separator]
            text_splitter = RecursiveCharacterTextSplitter(**splitter_kwargs)

            embeddings = await KBIngestionHelper._build_embeddings(embedding_provider, embedding_model, current_user)

            client = KBStorageHelper.get_fresh_chroma_client(kb_path)
            chroma = Chroma(
                client=client,
                embedding_function=embeddings,
                collection_name=kb_name,
            )

            job_id_str = str(task_job_id)
            for file_name, file_content in files_data:
                await logger.ainfo("Starting ingestion of %s for %s", file_name, kb_name)
                content = extract_text_from_bytes(file_name, file_content)
                if not content.strip():
                    continue

                chunks = text_splitter.split_text(content)
                for i in range(0, len(chunks), INGESTION_BATCH_SIZE):
                    if await KBIngestionHelper._is_job_cancelled(job_service, task_job_id):
                        raise IngestionCancelledError

                    batch = chunks[i : i + INGESTION_BATCH_SIZE]
                    docs = [
                        Document(
                            page_content=c,
                            metadata={
                                "source": source_name or file_name,
                                "file_name": file_name,
                                "chunk_index": i + j,
                                "total_chunks": len(chunks),
                                "ingested_at": datetime.now(timezone.utc).isoformat(),
                                "job_id": job_id_str,
                            },
                        )
                        for j, c in enumerate(batch)
                    ]

                    for attempt in range(MAX_RETRY_ATTEMPTS):
                        if await KBIngestionHelper._is_job_cancelled(job_service, task_job_id):
                            raise IngestionCancelledError
                        try:
                            await chroma.aadd_documents(docs)
                            break
                        except Exception as e:
                            if attempt == MAX_RETRY_ATTEMPTS - 1:
                                raise
                            wait = (attempt + 1) * EXPONENTIAL_BACKOFF_MULTIPLIER
                            await logger.awarning("Write failed, retrying in %ds: %s", wait, e)
                            await asyncio.sleep(wait)

                    await asyncio.sleep(0.01)

                total_chunks_created += len(chunks)
                processed_files.append(file_name)

            metadata = KBAnalysisHelper.get_metadata(kb_path, fast=True)
            KBAnalysisHelper.update_text_metrics(kb_path, metadata, chroma=chroma)
            metadata["size"] = KBStorageHelper.get_directory_size(kb_path)
            metadata["chunk_size"] = chunk_size
            metadata["chunk_overlap"] = chunk_overlap
            metadata["separator"] = separator or None
            metadata_path = kb_path / "embedding_metadata.json"
            new_source_types = list({f.rsplit(".", 1)[-1].lower() for f in processed_files if "." in f})
            existing_source_types = metadata.get("source_types", [])
            metadata["source_types"] = list(set(existing_source_types + new_source_types))
            metadata_path.write_text(json.dumps(metadata, indent=2))
            await logger.ainfo(f"Completed ingestion for {kb_name}")

            return {
                "message": f"Successfully ingested {len(processed_files)} file(s)",
                "files_processed": len(processed_files),
                "chunks_created": total_chunks_created,
            }

        except IngestionCancelledError:
            await logger.awarning(f"Ingestion job {task_job_id} was cancelled. Cleaning up partial data...")
            await KBIngestionHelper.cleanup_chroma_chunks_by_job(task_job_id, kb_path, kb_name)
            return {"message": "Job cancelled"}
        except Exception as e:
            await logger.aerror(f"Error in background ingestion: {e!s}. Initiating rollback...")
            await KBIngestionHelper.cleanup_chroma_chunks_by_job(task_job_id, kb_path, kb_name)
            raise
        finally:
            client = None
            chroma = None
            KBStorageHelper.release_chroma_resources(kb_path)