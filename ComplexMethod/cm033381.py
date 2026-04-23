async def create_dataset(tenant_id: str, req: dict):
    """
    Create a new dataset.

    :param tenant_id: tenant ID
    :param req: dataset creation request
    :return: (success, result) or (success, error_message)
    """
    # Extract ext field for additional parameters
    ext_fields = req.pop("ext", {})

    # Map auto_metadata_config (if provided) into parser_config structure
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
    req.update(ext_fields)

    e, create_dict = KnowledgebaseService.create_with_name(
        name=req.pop("name", None),
        tenant_id=tenant_id,
        parser_id=req.pop("parser_id", None),
        **req
    )

    if not e:
        return False, create_dict

    # Insert embedding model(embd id)
    ok, t = TenantService.get_by_id(tenant_id)
    if not ok:
        return False, "Tenant not found"
    if not create_dict.get("embd_id"):
        create_dict["embd_id"] = t.embd_id
    else:
        ok, err = verify_embedding_availability(create_dict["embd_id"], tenant_id)
        if not ok:
            return False, err

    if not KnowledgebaseService.save(**create_dict):
        return False, "Failed to save dataset"
    ok, k = KnowledgebaseService.get_by_id(create_dict["id"])
    if not ok:
        return False, "Dataset created failed"
    response_data = remap_dictionary_keys(k.to_dict())
    return True, response_data