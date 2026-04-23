def batched_doc_ids(
    checkpoint_connector_generator: CheckpointOutput[CT],
    batch_size: int,
) -> Generator[set[str], None, None]:
    batch: set[str] = set()
    for document, failure, next_checkpoint in CheckpointOutputWrapper[CT]()(
        checkpoint_connector_generator
    ):
        if document is not None:
            batch.add(document.id)
        elif (
            failure and failure.failed_document and failure.failed_document.document_id
        ):
            batch.add(failure.failed_document.document_id)

        if len(batch) >= batch_size:
            yield batch
            batch = set()
    if len(batch) > 0:
        yield batch