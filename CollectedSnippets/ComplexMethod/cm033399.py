def _parse_doc_id_filter_with_metadata(req, kb_id):
    """Parse document ID filter based on metadata conditions from the request.

    This function extracts and processes metadata filtering parameters from the request
    and returns a list of document IDs that match the specified criteria. It supports
    two filtering modes: simple metadata key-value matching and complex metadata
    conditions with operators.

    Args:
        req: The request object containing filtering parameters.
            - return_empty_metadata (bool|str): If True, returns all documents regardless
              of their metadata. Can be a boolean or string "true"/"false".
            - metadata_condition (str): JSON string containing complex metadata conditions
              with optional "logic" (and/or) and "conditions" list. Each condition should
              have "name" (key), "comparison_operator", and "value" fields.
            - metadata (str): JSON string containing key-value pairs for exact metadata
              matching. Values can be a single value or list of values (OR logic within
              same key). Can include special key "empty_metadata" to indicate documents
              with empty metadata.
        kb_id: The knowledge base ID to filter documents from.

    Returns:
        A tuple of (err_code, err_message, docs, return_empty_metadata):
            - err_code (int): Success code (RetCode.SUCCESS) if successful, or error code if validation fails.
            - err_message (str): Empty string if successful, or error message if validation fails.
            - docs (list): List of document IDs matching the metadata criteria,
              or empty list if no filter should be applied or on error.
            - return_empty_metadata (bool): The processed flag indicating whether to
              return documents with empty metadata.

    Note:
        - When both metadata and metadata_condition are provided, they are combined with AND logic.
        - The metadata_condition uses operators like: =, !=, >, <, >=, <=, contains, not contains,
          in, not in, start with, end with, empty, not empty.
        - The metadata parameter performs exact matching where values are OR'd within the same key
          & AND'd across different keys.

    Examples:
        Simple metadata filter (exact match):
            req = {"metadata": '{"author": ["John", "Jane"]}'}
            # Returns documents where author is John OR Jane

        Simple metadata filter with multiple keys:
            req = {"metadata": '{"author": "John", "status": "published"}'}
            # Returns documents where author is John AND status is published

        Complex metadata conditions:
            req = {"metadata_condition": '{"logic": "and", "conditions": [{"name": "status", "comparison_operator": "eq", "value": "published"}]}'}
            # Returns documents where status equals "published"

        Complex conditions with multiple operators:
            req = {"metadata_condition": '{"logic": "or", "conditions": [{"name": "priority", "comparison_operator": "=", "value": "high"}, {"name": "status", "comparison_operator": "contains", "value": "urgent"}]}'}
            # Returns documents where priority is high OR status contains "urgent"

        Return empty metadata:
            req = {"return_empty_metadata": True}
            # Returns all documents regardless of metadata

        Combined metadata and metadata_condition:
            req = {"metadata": '{"author": "John"}', "metadata_condition": '{"logic": "and", "conditions": [{"name": "status", "comparison_operator": "=", "value": "published"}]}'}
            # Returns documents where author is John AND status equals published
    """
    return_empty_metadata = req.get("return_empty_metadata", False)
    if isinstance(return_empty_metadata, str):
        return_empty_metadata = return_empty_metadata.lower() == "true"

    try:
        metadata_condition = json.loads(req.get("metadata_condition", "{}"))
    except json.JSONDecodeError:
        msg = f'metadata_condition must be valid JSON: {req.get("metadata_condition")}.'
        return RetCode.DATA_ERROR, msg, [], return_empty_metadata
    try:
        metadata = json.loads(req.get("metadata", "{}"))
    except json.JSONDecodeError:
        logging.error(msg=f'metadata must be valid JSON: {req.get("metadata")}.')
        return RetCode.DATA_ERROR, "metadata must be valid JSON.", [], return_empty_metadata

    if isinstance(metadata, dict) and metadata.get("empty_metadata"):
        return_empty_metadata = True
        metadata = {k: v for k, v in metadata.items() if k != "empty_metadata"}
    if return_empty_metadata:
        metadata_condition = {}
        metadata = {}
    else:
        if metadata_condition and not isinstance(metadata_condition, dict):
            return RetCode.DATA_ERROR, "metadata_condition must be an object.", [], return_empty_metadata
        if metadata and not isinstance(metadata, dict):
            return RetCode.DATA_ERROR, "metadata must be an object.", [], return_empty_metadata

    metas = dict()
    if metadata_condition or metadata:
        metas = DocMetadataService.get_flatted_meta_by_kbs([kb_id])

    doc_ids_filter = None
    if metadata_condition:
        doc_ids_filter = set(meta_filter(metas, convert_conditions(metadata_condition), metadata_condition.get("logic", "and")))
        if metadata_condition.get("conditions") and not doc_ids_filter:
            return RetCode.SUCCESS, "", [], return_empty_metadata

    if metadata:
        metadata_doc_ids = None
        for key, values in metadata.items():
            if not values:
                continue
            if not isinstance(values, list):
                values = [values]
            values = [str(v) for v in values if v is not None and str(v).strip()]
            if not values:
                continue
            key_doc_ids = set()
            for value in values:
                key_doc_ids.update(metas.get(key, {}).get(value, []))
            if metadata_doc_ids is None:
                metadata_doc_ids = key_doc_ids
            else:
                metadata_doc_ids &= key_doc_ids
            if not metadata_doc_ids:
                return RetCode.SUCCESS, "", [], return_empty_metadata

        if metadata_doc_ids is not None:
            if doc_ids_filter is None:
                doc_ids_filter = metadata_doc_ids
            else:
                doc_ids_filter &= metadata_doc_ids
            if not doc_ids_filter:
                return RetCode.SUCCESS, "", [], return_empty_metadata

    return RetCode.SUCCESS, "", list(doc_ids_filter) if doc_ids_filter is not None else [], return_empty_metadata