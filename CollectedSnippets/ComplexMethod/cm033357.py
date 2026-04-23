async def switch_chunks(tenant_id, dataset_id, document_id):
    """
    Switch availability of specified chunks (same as chunk_app switch).
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
        required: true
        schema:
          type: object
          properties:
            chunk_ids:
              type: array
              items:
                type: string
              description: List of chunk IDs to switch.
            available_int:
              type: integer
              description: 1 for available, 0 for unavailable.
            available:
              type: boolean
              description: Availability status (alternative to available_int).
      - in: header
        name: Authorization
        type: string
        required: true
        description: Bearer token for authentication.
    responses:
      200:
        description: Chunks availability switched successfully.
    """
    if not KnowledgebaseService.accessible(kb_id=dataset_id, user_id=tenant_id):
        return get_error_data_result(message=f"You don't own the dataset {dataset_id}.")
    req = await get_request_json()
    if not req.get("chunk_ids"):
        return get_error_data_result(message="`chunk_ids` is required.")
    if "available_int" not in req and "available" not in req:
        return get_error_data_result(message="`available_int` or `available` is required.")
    available_int = int(req["available_int"]) if "available_int" in req else (1 if req.get("available") else 0)
    try:

        def _switch_sync():
            e, doc = DocumentService.get_by_id(document_id)
            if not e:
                return get_error_data_result(message="Document not found!")
            if not doc or str(doc.kb_id) != str(dataset_id):
                return get_error_data_result(message="Document not found!")
            for cid in req["chunk_ids"]:
                if not settings.docStoreConn.update(
                    {"id": cid},
                    {"available_int": available_int},
                    search.index_name(tenant_id),
                    doc.kb_id,
                ):
                    return get_error_data_result(message="Index updating failure")
            return get_result(data=True)

        return await thread_pool_exec(_switch_sync)
    except Exception as e:
        return server_error_response(e)