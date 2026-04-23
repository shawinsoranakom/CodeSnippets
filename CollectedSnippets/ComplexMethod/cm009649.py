def index(
    docs_source: BaseLoader | Iterable[Document],
    record_manager: RecordManager,
    vector_store: VectorStore | DocumentIndex,
    *,
    batch_size: int = 100,
    cleanup: Literal["incremental", "full", "scoped_full"] | None = None,
    source_id_key: str | Callable[[Document], str] | None = None,
    cleanup_batch_size: int = 1_000,
    force_update: bool = False,
    key_encoder: Literal["sha1", "sha256", "sha512", "blake2b"]
    | Callable[[Document], str] = "sha1",
    upsert_kwargs: dict[str, Any] | None = None,
) -> IndexingResult:
    """Index data from the loader into the vector store.

    Indexing functionality uses a manager to keep track of which documents
    are in the vector store.

    This allows us to keep track of which documents were updated, and which
    documents were deleted, which documents should be skipped.

    For the time being, documents are indexed using their hashes, and users
    are not able to specify the uid of the document.

    !!! warning "Behavior changed in `langchain-core` 0.3.25"

        Added `scoped_full` cleanup mode.

    !!! warning

        * In full mode, the loader should be returning
            the entire dataset, and not just a subset of the dataset.
            Otherwise, the auto_cleanup will remove documents that it is not
            supposed to.
        * In incremental mode, if documents associated with a particular
            source id appear across different batches, the indexing API
            will do some redundant work. This will still result in the
            correct end state of the index, but will unfortunately not be
            100% efficient. For example, if a given document is split into 15
            chunks, and we index them using a batch size of 5, we'll have 3 batches
            all with the same source id. In general, to avoid doing too much
            redundant work select as big a batch size as possible.
        * The `scoped_full` mode is suitable if determining an appropriate batch size
            is challenging or if your data loader cannot return the entire dataset at
            once. This mode keeps track of source IDs in memory, which should be fine
            for most use cases. If your dataset is large (10M+ docs), you will likely
            need to parallelize the indexing process regardless.

    Args:
        docs_source: Data loader or iterable of documents to index.
        record_manager: Timestamped set to keep track of which documents were
            updated.
        vector_store: `VectorStore` or DocumentIndex to index the documents into.
        batch_size: Batch size to use when indexing.
        cleanup: How to handle clean up of documents.

            - incremental: Cleans up all documents that haven't been updated AND
                that are associated with source IDs that were seen during indexing.
                Clean up is done continuously during indexing helping to minimize the
                probability of users seeing duplicated content.
            - full: Delete all documents that have not been returned by the loader
                during this run of indexing.
                Clean up runs after all documents have been indexed.
                This means that users may see duplicated content during indexing.
            - scoped_full: Similar to Full, but only deletes all documents
                that haven't been updated AND that are associated with
                source IDs that were seen during indexing.
            - None: Do not delete any documents.
        source_id_key: Optional key that helps identify the original source
            of the document.
        cleanup_batch_size: Batch size to use when cleaning up documents.
        force_update: Force update documents even if they are present in the
            record manager. Useful if you are re-indexing with updated embeddings.
        key_encoder: Hashing algorithm to use for hashing the document content and
            metadata. Options include "blake2b", "sha256", and "sha512".

            !!! version-added "Added in `langchain-core` 0.3.66"

        key_encoder: Hashing algorithm to use for hashing the document.
            If not provided, a default encoder using SHA-1 will be used.
            SHA-1 is not collision-resistant, and a motivated attacker
            could craft two different texts that hash to the
            same cache key.

            New applications should use one of the alternative encoders
            or provide a custom and strong key encoder function to avoid this risk.

            When changing the key encoder, you must change the
            index as well to avoid duplicated documents in the cache.
        upsert_kwargs: Additional keyword arguments to pass to the add_documents
            method of the `VectorStore` or the upsert method of the DocumentIndex.
            For example, you can use this to specify a custom vector_field:
            upsert_kwargs={"vector_field": "embedding"}
            !!! version-added "Added in `langchain-core` 0.3.10"

    Returns:
        Indexing result which contains information about how many documents
        were added, updated, deleted, or skipped.

    Raises:
        ValueError: If cleanup mode is not one of 'incremental', 'full' or None
        ValueError: If cleanup mode is incremental and source_id_key is None.
        ValueError: If `VectorStore` does not have
            "delete" and "add_documents" required methods.
        ValueError: If source_id_key is not None, but is not a string or callable.
        TypeError: If `vectorstore` is not a `VectorStore` or a DocumentIndex.
        AssertionError: If `source_id` is None when cleanup mode is incremental.
            (should be unreachable code).
    """
    # Behavior is deprecated, but we keep it for backwards compatibility.
    # # Warn only once per process.
    if key_encoder == "sha1":
        _warn_about_sha1()

    if cleanup not in {"incremental", "full", "scoped_full", None}:
        msg = (
            f"cleanup should be one of 'incremental', 'full', 'scoped_full' or None. "
            f"Got {cleanup}."
        )
        raise ValueError(msg)

    if (cleanup in {"incremental", "scoped_full"}) and source_id_key is None:
        msg = (
            "Source id key is required when cleanup mode is incremental or scoped_full."
        )
        raise ValueError(msg)

    destination = vector_store  # Renaming internally for clarity

    # If it's a vectorstore, let's check if it has the required methods.
    if isinstance(destination, VectorStore):
        # Check that the Vectorstore has required methods implemented
        methods = ["delete", "add_documents"]

        for method in methods:
            if not hasattr(destination, method):
                msg = (
                    f"Vectorstore {destination} does not have required method {method}"
                )
                raise ValueError(msg)

        if type(destination).delete == VectorStore.delete:
            # Checking if the VectorStore has overridden the default delete method
            # implementation which just raises a NotImplementedError
            msg = "Vectorstore has not implemented the delete method"
            raise ValueError(msg)
    elif isinstance(destination, DocumentIndex):
        pass
    else:
        msg = (
            f"Vectorstore should be either a VectorStore or a DocumentIndex. "
            f"Got {type(destination)}."
        )
        raise TypeError(msg)

    if isinstance(docs_source, BaseLoader):
        try:
            doc_iterator = docs_source.lazy_load()
        except NotImplementedError:
            doc_iterator = iter(docs_source.load())
    else:
        doc_iterator = iter(docs_source)

    source_id_assigner = _get_source_id_assigner(source_id_key)

    # Mark when the update started.
    index_start_dt = record_manager.get_time()
    num_added = 0
    num_skipped = 0
    num_updated = 0
    num_deleted = 0
    scoped_full_cleanup_source_ids: set[str] = set()

    for doc_batch in _batch(batch_size, doc_iterator):
        # Track original batch size before deduplication
        original_batch_size = len(doc_batch)

        hashed_docs = list(
            _deduplicate_in_order(
                [
                    _get_document_with_hash(doc, key_encoder=key_encoder)
                    for doc in doc_batch
                ]
            )
        )
        # Count documents removed by within-batch deduplication
        num_skipped += original_batch_size - len(hashed_docs)

        source_ids: Sequence[str | None] = [
            source_id_assigner(hashed_doc) for hashed_doc in hashed_docs
        ]

        if cleanup in {"incremental", "scoped_full"}:
            # Source IDs are required.
            for source_id, hashed_doc in zip(source_ids, hashed_docs, strict=False):
                if source_id is None:
                    msg = (
                        f"Source IDs are required when cleanup mode is "
                        f"incremental or scoped_full. "
                        f"Document that starts with "
                        f"content: {hashed_doc.page_content[:100]} "
                        f"was not assigned as source id."
                    )
                    raise ValueError(msg)
                if cleanup == "scoped_full":
                    scoped_full_cleanup_source_ids.add(source_id)
            # Source IDs cannot be None after for loop above.
            source_ids = cast("Sequence[str]", source_ids)

        exists_batch = record_manager.exists(
            cast("Sequence[str]", [doc.id for doc in hashed_docs])
        )

        # Filter out documents that already exist in the record store.
        uids = []
        docs_to_index = []
        uids_to_refresh = []
        seen_docs: set[str] = set()
        for hashed_doc, doc_exists in zip(hashed_docs, exists_batch, strict=False):
            hashed_id = cast("str", hashed_doc.id)
            if doc_exists:
                if force_update:
                    seen_docs.add(hashed_id)
                else:
                    uids_to_refresh.append(hashed_id)
                    continue
            uids.append(hashed_id)
            docs_to_index.append(hashed_doc)

        # Update refresh timestamp
        if uids_to_refresh:
            record_manager.update(uids_to_refresh, time_at_least=index_start_dt)
            num_skipped += len(uids_to_refresh)

        # Be pessimistic and assume that all vector store write will fail.
        # First write to vector store
        if docs_to_index:
            if isinstance(destination, VectorStore):
                destination.add_documents(
                    docs_to_index,
                    ids=uids,
                    batch_size=batch_size,
                    **(upsert_kwargs or {}),
                )
            elif isinstance(destination, DocumentIndex):
                destination.upsert(
                    docs_to_index,
                    **(upsert_kwargs or {}),
                )

            num_added += len(docs_to_index) - len(seen_docs)
            num_updated += len(seen_docs)

        # And only then update the record store.
        # Update ALL records, even if they already exist since we want to refresh
        # their timestamp.
        record_manager.update(
            cast("Sequence[str]", [doc.id for doc in hashed_docs]),
            group_ids=source_ids,
            time_at_least=index_start_dt,
        )

        # If source IDs are provided, we can do the deletion incrementally!
        if cleanup == "incremental":
            # Get the uids of the documents that were not returned by the loader.
            # mypy isn't good enough to determine that source IDs cannot be None
            # here due to a check that's happening above, so we check again.
            for source_id in source_ids:
                if source_id is None:
                    msg = (
                        "source_id cannot be None at this point. "
                        "Reached unreachable code."
                    )
                    raise AssertionError(msg)

            source_ids_ = cast("Sequence[str]", source_ids)

            while uids_to_delete := record_manager.list_keys(
                group_ids=source_ids_, before=index_start_dt, limit=cleanup_batch_size
            ):
                # Then delete from vector store.
                _delete(destination, uids_to_delete)
                # First delete from record store.
                record_manager.delete_keys(uids_to_delete)
                num_deleted += len(uids_to_delete)

    if cleanup == "full" or (
        cleanup == "scoped_full" and scoped_full_cleanup_source_ids
    ):
        delete_group_ids: Sequence[str] | None = None
        if cleanup == "scoped_full":
            delete_group_ids = list(scoped_full_cleanup_source_ids)
        while uids_to_delete := record_manager.list_keys(
            group_ids=delete_group_ids, before=index_start_dt, limit=cleanup_batch_size
        ):
            # First delete from record store.
            _delete(destination, uids_to_delete)
            # Then delete from record manager.
            record_manager.delete_keys(uids_to_delete)
            num_deleted += len(uids_to_delete)

    return {
        "num_added": num_added,
        "num_updated": num_updated,
        "num_skipped": num_skipped,
        "num_deleted": num_deleted,
    }