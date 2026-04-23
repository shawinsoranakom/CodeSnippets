def _get_docs_with_request(req, dataset_id:str):
    """Get documents with request parameters from a dataset.

    This function extracts filtering parameters from the request and returns
    a list of documents matching the specified criteria.

    Args:
        req: The request object containing query parameters.
            - page (int): Page number for pagination (default: 1).
            - page_size (int): Number of documents per page (default: 30).
            - orderby (str): Field to order by (default: "create_time").
            - desc (bool): Whether to order in descending order (default: True).
            - keywords (str): Keywords to search in document names.
            - suffix (list): File suffix filters.
            - types (list): Document type filters.
            - run (list): Processing status filters.
            - create_time_from (int): Start timestamp for time range filter.
            - create_time_to (int): End timestamp for time range filter.
            - return_empty_metadata (bool|str): Whether to return documents with empty metadata.
            - metadata_condition (str): JSON string for complex metadata conditions.
            - metadata (str): JSON string for simple metadata key-value matching.
        dataset_id: The dataset ID to retrieve documents from.

    Returns:
        A tuple of (err_code, err_message, docs, total):
            - err_code (int): Success code (RetCode.SUCCESS) if successful, or error code if validation fails.
            - err_message (str): Empty string if successful, or error message if validation fails.
            - docs (list): List of document dictionaries matching the criteria, or empty list on error.
            - total (int): Total number of documents matching the criteria.

    Note:
        - The function supports filtering by document types, processing status, keywords, and time range.
        - Metadata filtering supports both simple key-value matching and complex conditions with operators.
    """
    q = req.args

    page = int(q.get("page", 1))
    page_size = int(q.get("page_size", 30))

    orderby = q.get("orderby", "create_time")
    desc = str(q.get("desc", "true")).strip().lower() != "false"
    keywords = q.get("keywords", "")

    # filters - align with OpenAPI parameter names
    suffix = q.getlist("suffix")

    types = q.getlist("types")
    if types:
        invalid_types = {t for t in types if t not in VALID_FILE_TYPES}
        if invalid_types:
            msg = f"Invalid filter conditions: {', '.join(invalid_types)} type{'s' if len(invalid_types) > 1 else ''}"
            return RetCode.DATA_ERROR, msg, [], 0

    # map run status (text or numeric) - align with API parameter
    run_status = q.getlist("run")
    run_status_text_to_numeric = {"UNSTART": "0", "RUNNING": "1", "CANCEL": "2", "DONE": "3", "FAIL": "4"}
    run_status_converted = [run_status_text_to_numeric.get(v, v) for v in run_status]
    if run_status_converted:
        invalid_status = {s for s in run_status_converted if s not in run_status_text_to_numeric.values()}
        if invalid_status:
            msg = f"Invalid filter run status conditions: {', '.join(invalid_status)}"
            return RetCode.DATA_ERROR, msg, [], 0

    err_code, err_message, doc_ids_filter, return_empty_metadata = _parse_doc_id_filter_with_metadata(q, dataset_id)
    if err_code != RetCode.SUCCESS:
        return err_code, err_message, [], 0

    doc_name = q.get("name")
    doc_id = q.get("id")
    if doc_id:
        if not DocumentService.query(id=doc_id, kb_id=dataset_id):
            return RetCode.DATA_ERROR, f"You don't own the document {doc_id}.", [], 0
        doc_ids_filter = [doc_id] # id provided, ignore other filters
    if doc_name and not DocumentService.query(name=doc_name, kb_id=dataset_id):
        return RetCode.DATA_ERROR, f"You don't own the document {doc_name}.", [], 0

    doc_ids = q.getlist("ids")
    if doc_id and len(doc_ids) > 0:
        return RetCode.DATA_ERROR, f"Should not provide both 'id':{doc_id} and 'ids'{doc_ids}"
    if len(doc_ids) > 0:
        doc_ids_filter = doc_ids

    docs, total = DocumentService.get_by_kb_id(dataset_id, page, page_size, orderby, desc, keywords, run_status_converted, types, suffix,
                                               name=doc_name, doc_ids=doc_ids_filter, return_empty_metadata=return_empty_metadata)

    # time range filter (0 means no bound)
    create_time_from = int(q.get("create_time_from", 0))
    create_time_to = int(q.get("create_time_to", 0))
    if create_time_from or create_time_to:
        docs = [d for d in docs if (create_time_from == 0 or d.get("create_time", 0) >= create_time_from) and (create_time_to == 0 or d.get("create_time", 0) <= create_time_to)]

    return RetCode.SUCCESS, "", docs, total