def _aggregate_filters(docs):
    """Aggregate filter options from a list of documents.

    This function processes a list of document dictionaries and aggregates
    available filter values for building filter UI on the client side.

    Args:
        docs (list): List of document dictionaries, each containing:
            - id (str): Document ID
            - suffix (str): File extension (e.g., "pdf", "docx")
            - run (int): Parsing status code (0=UNSTART, 1=RUNNING, 2=CANCEL, 3=DONE, 4=FAIL)

    Returns:
        tuple: A tuple containing:
            - dict: Aggregated filter options with keys:
                - suffix: Dict mapping file extensions to document counts
                - run_status: Dict mapping status codes to document counts
                - metadata: Dict mapping metadata field names to value counts
            - int: Total number of documents processed
    """
    suffix_counter = {}
    run_status_counter = {}
    metadata_counter = {}
    empty_metadata_count = 0

    for doc in docs:
        suffix_counter[doc.get("suffix")] = suffix_counter.get(doc.get("suffix"), 0) + 1
        key_of_run = str(doc.get("run"))
        run_status_counter[key_of_run] = run_status_counter.get(key_of_run, 0) + 1
        meta_fields = doc.get("meta_fields", {})

        if not meta_fields:
            empty_metadata_count += 1
            continue
        has_valid_meta = False

        for key, value in meta_fields.items():
            values = value if isinstance(value, list) else [value]
            for vv in values:
                if vv is None:
                    continue
                if isinstance(vv, str) and not vv.strip():
                    continue
                sv = str(vv)
                if key not in metadata_counter:
                    metadata_counter[key] = {}
                metadata_counter[key][sv] = metadata_counter[key].get(sv, 0) + 1
                has_valid_meta = True
        if not has_valid_meta:
            empty_metadata_count += 1

    metadata_counter["empty_metadata"] = {"true": empty_metadata_count}
    return {
        "suffix": suffix_counter,
        "run_status": run_status_counter,
        "metadata": metadata_counter,
    }