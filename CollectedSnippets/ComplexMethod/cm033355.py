async def rm_chunk(tenant_id, dataset_id, document_id):
    """
    Remove chunks from a document.
    ---
    tags:
      - Chunks
    security:
      - ApiKeyAuth: []
    parameters:
      - in: path
        name: dataset_id
        type: string
        required: true
        description: ID of the dataset.
      - in: path
        name: document_id
        type: string
        required: true
        description: ID of the document.
      - in: body
        name: body
        description: Chunk removal parameters.
        required: true
        schema:
          type: object
          properties:
            chunk_ids:
              type: array
              items:
                type: string
              description: |
                List of chunk IDs to remove.
                If omitted, `null`, or an empty array is provided, no chunks will be deleted.
      - in: header
        name: Authorization
        type: string
        required: true
        description: Bearer token for authentication.
    responses:
      200:
        description: Chunks removed successfully.
        schema:
          type: object
    """
    if not KnowledgebaseService.accessible(kb_id=dataset_id, user_id=tenant_id):
        return get_error_data_result(message=f"You don't own the dataset {dataset_id}.")
    docs = DocumentService.get_by_ids([document_id])
    if not docs:
        raise LookupError(f"Can't find the document with ID {document_id}!")
    req = await get_request_json()
    if not req:
        return get_result()

    chunk_ids = req.get("chunk_ids")
    if not chunk_ids:
        if req.get("delete_all") is True:
            doc = docs[0]
            # Clean up storage assets while index rows still exist for discovery
            DocumentService.delete_chunk_images(doc, tenant_id)
            condition = {"doc_id": document_id}
            chunk_number = settings.docStoreConn.delete(condition, search.index_name(tenant_id), dataset_id)
            if chunk_number != 0:
                DocumentService.decrement_chunk_num(document_id, dataset_id, 1, chunk_number, 0)
            return get_result(message=f"deleted {chunk_number} chunks")
        else:
            return get_result()

    condition = {"doc_id": document_id}
    unique_chunk_ids, duplicate_messages = check_duplicate_ids(chunk_ids, "chunk")
    condition["id"] = unique_chunk_ids
    chunk_number = settings.docStoreConn.delete(condition, search.index_name(tenant_id), dataset_id)
    if chunk_number != 0:
        DocumentService.decrement_chunk_num(document_id, dataset_id, 1, chunk_number, 0)
    if chunk_number != len(unique_chunk_ids):
        if len(unique_chunk_ids) == 0:
            return get_result(message=f"deleted {chunk_number} chunks")
        return get_error_data_result(message=f"rm_chunk deleted chunks {chunk_number}, expect {len(unique_chunk_ids)}")
    if duplicate_messages:
        return get_result(
            message=f"Partially deleted {chunk_number} chunks with {len(duplicate_messages)} errors",
            data={"success_count": chunk_number, "errors": duplicate_messages},
        )
    return get_result(message=f"deleted {chunk_number} chunks")