async def update_document(tenant_id, dataset_id, document_id):
    """
    Update a document within a dataset.
    ---
    tags:
      - Documents
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
        description: ID of the document to update.
      - in: header
        name: Authorization
        type: string
        required: true
        description: Bearer token for authentication.
      - in: body
        name: body
        description: Document update parameters.
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              description: New name of the document.
            parser_config:
              type: object
              description: Parser configuration.
            chunk_method:
              type: string
              description: Chunking method.
            enabled:
              type: boolean
              description: Document status.
    responses:
      200:
        description: Document updated successfully.
        schema:
          type: object
    """
    req = await get_request_json()

    # Verify ownership and existence of dataset and document
    if not KnowledgebaseService.query(id=dataset_id, tenant_id=tenant_id):
        return get_error_data_result(message="You don't own the dataset.")
    e, kb = KnowledgebaseService.get_by_id(dataset_id)
    if not e:
        return get_error_data_result(message="Can't find this dataset!")

    # Prepare data for validation
    docs = DocumentService.query(kb_id=dataset_id, id=document_id)
    if not docs:
        return get_error_data_result(message="The dataset doesn't own the document.")

    # Validate document update request parameters
    try:
        update_doc_req = UpdateDocumentReq(**req)
    except ValidationError as e:
        return get_error_data_result(message=format_validation_error_message(e), code=RetCode.DATA_ERROR)

    doc = docs[0]

    # further check with inner status (from DB)
    error_msg, error_code = validate_document_update_fields(update_doc_req, doc, req)
    if error_msg:
        return get_error_data_result(message=error_msg, code=error_code)

    # All validations passed, now perform all updates
    # meta_fields provided, then update it
    if "meta_fields" in req:
        if not DocMetadataService.update_document_metadata(document_id, update_doc_req.meta_fields):
            return get_error_data_result(message="Failed to update metadata")
    # doc name provided from request and diff with existing value, update
    if "name" in req and req["name"] != doc.name:
        if error := update_document_name_only(document_id, req["name"]):
            return error

    # parser config provided (already validated in UpdateDocumentReq), update it
    if update_doc_req.parser_config:
        DocumentService.update_parser_config(doc.id, req["parser_config"])

    # chunk method provided - the update method will check if it's different with existing one
    if update_doc_req.chunk_method:
        if error := update_chunk_method_only(req, doc, dataset_id, tenant_id):
            return error

    if "enabled" in req: # already checked in UpdateDocumentReq - it's int if it's present
        # "enabled" flag provided, the update method will check if it's changed and then update if so
        if error := update_document_status_only(int(req["enabled"]), doc, kb):
            return error

    try:
        original_doc_id = doc.id
        ok, doc = DocumentService.get_by_id(doc.id)
        if not ok:
            return get_error_data_result(message=f"Can not get document by id:{original_doc_id}")
    except OperationalError as e:
        logging.exception(e)
        return get_error_data_result(message="Database operation failed")
    renamed_doc = map_doc_keys(doc)
    return get_result(data=renamed_doc)