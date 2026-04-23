async def update_dataset(tenant_id: str, dataset_id: str, req: dict):
    """
    Update a dataset.

    :param tenant_id: tenant ID
    :param dataset_id: dataset ID
    :param req: dataset update request
    :return: (success, result) or (success, error_message)
    """
    if not req:
        return False, "No properties were modified"

    kb = KnowledgebaseService.get_or_none(id=dataset_id, tenant_id=tenant_id)
    if kb is None:
        return False, f"User '{tenant_id}' lacks permission for dataset '{dataset_id}'"

    # Extract ext field for additional parameters
    ext_fields = req.pop("ext", {})

    # Map auto_metadata_config into parser_config if present
    auto_meta = req.pop("auto_metadata_config", {})
    if auto_meta:
        parser_cfg = req.get("parser_config") or {}
        fields = []
        for f in auto_meta.get("fields", []):
            fields.append(
                {
                    "name": f.get("name", ""),
                    "type": f.get("type", ""),
                    "description": f.get("description"),
                    "examples": f.get("examples"),
                    "restrict_values": f.get("restrict_values", False),
                }
            )
        parser_cfg["metadata"] = fields
        parser_cfg["enable_metadata"] = auto_meta.get("enabled", True)
        req["parser_config"] = parser_cfg

    # Merge ext fields with req
    req.update(ext_fields)

    # Extract connectors from request
    connectors = []
    if "connectors" in req:
        connectors = req["connectors"]
        del req["connectors"]

    if req.get("parser_config"):
        # Flatten parent_child config into children_delimiter for the execution layer
        pc = req["parser_config"].get("parent_child", {})
        if pc.get("use_parent_child"):
            req["parser_config"]["children_delimiter"] = pc.get("children_delimiter", "\n")
            req["parser_config"]["enable_children"] = pc.get("use_parent_child", True)
        else:
            req["parser_config"]["children_delimiter"] = ""
            req["parser_config"]["enable_children"] = False
            req["parser_config"]["parent_child"] = {}

        parser_config = req["parser_config"]
        req_ext_fields = parser_config.pop("ext", {})
        parser_config.update(req_ext_fields)
        req["parser_config"] = deep_merge(kb.parser_config, parser_config)

    if (chunk_method := req.get("parser_id")) and chunk_method != kb.parser_id:
        if not req.get("parser_config"):
            req["parser_config"] = get_parser_config(chunk_method, None)
    elif "parser_config" in req and not req["parser_config"]:
        del req["parser_config"]

    if kb.pipeline_id and req.get("parser_id") and not req.get("pipeline_id"):
        # shift to use parser_id, delete old pipeline_id
        req["pipeline_id"] = ""

    if "name" in req and req["name"].lower() != kb.name.lower():
        exists = KnowledgebaseService.get_or_none(name=req["name"], tenant_id=tenant_id,
                                                  status=StatusEnum.VALID.value)
        if exists:
            return False, f"Dataset name '{req['name']}' already exists"

    if "embd_id" in req:
        if not req["embd_id"]:
            req["embd_id"] = kb.embd_id
        if kb.chunk_num != 0 and req["embd_id"] != kb.embd_id:
            return False, f"When chunk_num ({kb.chunk_num}) > 0, embedding_model must remain {kb.embd_id}"
        ok, err = verify_embedding_availability(req["embd_id"], tenant_id)
        if not ok:
            return False, err

    if "pagerank" in req and req["pagerank"] != kb.pagerank:
        if os.environ.get("DOC_ENGINE", "elasticsearch") == "infinity":
            return False, "'pagerank' can only be set when doc_engine is elasticsearch"

        if req["pagerank"] > 0:
            from rag.nlp import search
            settings.docStoreConn.update({"kb_id": kb.id}, {PAGERANK_FLD: req["pagerank"]},
                                         search.index_name(kb.tenant_id), kb.id)
        else:
            # Elasticsearch requires PAGERANK_FLD be non-zero!
            from rag.nlp import search
            settings.docStoreConn.update({"exists": PAGERANK_FLD}, {"remove": PAGERANK_FLD},
                                         search.index_name(kb.tenant_id), kb.id)
    if "parse_type" in req:
        del req["parse_type"]

    if not KnowledgebaseService.update_by_id(kb.id, req):
        return False, "Update dataset error.(Database error)"

    ok, k = KnowledgebaseService.get_by_id(kb.id)
    if not ok:
        return False, "Dataset updated failed"

    # Link connectors to the dataset
    errors = Connector2KbService.link_connectors(kb.id, [conn for conn in connectors], tenant_id)
    if errors:
        logging.error("Link KB errors: %s", errors)

    response_data = remap_dictionary_keys(k.to_dict())
    response_data["connectors"] = connectors
    return True, response_data