async def upload_document(dataset_id, tenant_id):
    """
    Upload documents to a dataset.
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
      - in: header
        name: Authorization
        type: string
        required: true
        description: Bearer token for authentication.
      - in: formData
        name: file
        type: file
        required: true
        description: Document files to upload.
      - in: formData
        name: parent_path
        type: string
        description: Optional nested path under the parent folder. Uses '/' separators.
      - in: query
        name: return_raw_files
        type: boolean
        required: false
        default: false
        description: Whether to skip document key mapping and return raw document data
    responses:
      200:
        description: Successfully uploaded documents.
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                    description: Document ID.
                  name:
                    type: string
                    description: Document name.
                  chunk_count:
                    type: integer
                    description: Number of chunks.
                  token_count:
                    type: integer
                    description: Number of tokens.
                  dataset_id:
                    type: string
                    description: ID of the dataset.
                  chunk_method:
                    type: string
                    description: Chunking method used.
                  run:
                    type: string
                    description: Processing status.
    """
    from api.constants import FILE_NAME_LEN_LIMIT
    from api.db.services.file_service import FileService

    form = await request.form
    files = await request.files

    # Validation
    if "file" not in files:
        logging.error("No file part!")
        return get_error_data_result(message="No file part!", code=RetCode.ARGUMENT_ERROR)

    file_objs = files.getlist("file")
    for file_obj in file_objs:
        if file_obj is None or file_obj.filename is None or file_obj.filename == "":
            logging.error("No file selected!")
            return get_error_data_result(message="No file selected!", code=RetCode.ARGUMENT_ERROR)
        if len(file_obj.filename.encode("utf-8")) > FILE_NAME_LEN_LIMIT:
            msg = f"File name must be {FILE_NAME_LEN_LIMIT} bytes or less."
            logging.error(msg)
            return get_error_data_result(message=msg, code=RetCode.ARGUMENT_ERROR)

    # KB Lookup
    e, kb = KnowledgebaseService.get_by_id(dataset_id)
    if not e:
        logging.error(f"Can't find the dataset with ID {dataset_id}!")
        return get_error_data_result(message=f"Can't find the dataset with ID {dataset_id}!", code=RetCode.DATA_ERROR)

    # Permission Check
    if not check_kb_team_permission(kb, tenant_id):
        logging.error("No authorization.")
        return get_error_data_result(message="No authorization.", code=RetCode.AUTHENTICATION_ERROR)

    # File Upload (async)
    err, files = await thread_pool_exec(
        FileService.upload_document, kb, file_objs, tenant_id,
        parent_path=form.get("parent_path")
    )
    if err:
        msg = "\n".join(err)
        logging.error(msg)
        return get_error_data_result(message=msg, code=RetCode.SERVER_ERROR)

    if not files:
        msg = "There seems to be an issue with your file format. please verify it is correct and not corrupted."
        logging.error(msg)
        return get_error_data_result(message=msg, code=RetCode.DATA_ERROR)

    files = [f[0] for f in files]  # remove the blob

    # Check if we should return raw files without document key mapping
    return_raw_files = request.args.get("return_raw_files", "false").lower() == "true"

    if return_raw_files:
        return get_result(data=files)

    renamed_doc_list = [map_doc_keys_with_run_status(doc, run_status="0") for doc in files]
    return get_result(data=renamed_doc_list)