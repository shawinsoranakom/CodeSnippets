async def delete_documents(tenant_id, dataset_id):
    """
    Delete documents from a dataset.
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
        description: ID of the dataset containing the documents.
      - in: header
        name: Authorization
        type: string
        required: true
        description: Bearer token for authentication.
      - in: body
        name: body
        description: Document deletion parameters.
        required: true
        schema:
          type: object
          properties:
            ids:
              type: array or null
              items:
                type: string
              description: |
                Specifies the documents to delete:
                - An array of IDs, only the specified documents will be deleted.
            delete_all:
              type: boolean
              default: false
              description: Whether to delete all documents in the dataset.
    responses:
      200:
        description: Successful operation.
        schema:
          type: object
    """
    req, err = await validate_and_parse_json_request(request, DeleteDocumentReq)
    if err is not None or req is None:
        return get_error_argument_result(err)

    try:
        # Validate dataset exists and user has permission
        if not KnowledgebaseService.accessible(kb_id=dataset_id, user_id=tenant_id):
            return get_error_data_result(message=f"You don't own the dataset {dataset_id}. ")

        # Get documents to delete
        doc_ids = req.get("ids") or []
        delete_all = req.get("delete_all", False)
        if not delete_all and len(doc_ids) == 0:
            return get_error_data_result(message=f"should either provide doc ids or set delete_all(true), dataset: {dataset_id}. ")

        if len(doc_ids) > 0 and delete_all:
            return get_error_data_result(message=f"should not provide both doc ids and delete_all(true), dataset: {dataset_id}. ")
        if delete_all:
            doc_ids = [doc.id for doc in DocumentService.query(kb_id=dataset_id)]

        # make sure each id is unique
        unique_doc_ids, duplicate_messages = check_duplicate_ids(doc_ids, "document")
        if duplicate_messages:
            logging.warning(f"duplicate_messages:{duplicate_messages}")
        else:
            doc_ids = unique_doc_ids

        # Delete documents using existing FileService.delete_docs
        errors = await thread_pool_exec(FileService.delete_docs, doc_ids, tenant_id)

        if errors:
            return get_error_data_result(message=str(errors))

        return get_result(data={"deleted": len(doc_ids)})
    except Exception as e:
        logging.exception(e)
        return get_error_data_result(message="Internal server error")