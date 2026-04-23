def build_hierarchy_to_codelist_map(hierarchies: dict) -> dict[str, str]:
    """
    Build mapping from hierarchy ID to codelist ID.

    Parameters
    ----------
    hierarchies : dict
        Dictionary of hierarchy_id -> hierarchy data.

    Returns
    -------
    dict[str, str]
        Mapping from hierarchy ID to its primary codelist ID.
    """
    mapping: dict[str, str] = {}
    for hierarchy_id, hierarchy in hierarchies.items():
        codelist_id = None

        # Method 1: Check owningCodelistUrn annotation
        annotations = hierarchy.get("annotations", [])
        for annotation in annotations:
            if annotation.get("id") == "owningCodelistUrn":
                urn = annotation.get("text", "")
                codelist_id = parse_codelist_urn(urn)
                if codelist_id:
                    break

        # Method 2: Infer from first hierarchicalCode's code URN
        # Handles hierarchies like H_QGFS_* that don't have owningCodelistUrn
        if not codelist_id:
            hcodes = hierarchy.get("hierarchicalCodes", [])
            if hcodes and isinstance(hcodes, list) and hcodes:
                first_code = hcodes[0]
                code_urn = first_code.get("code", "")
                if code_urn:
                    codelist_id = parse_codelist_id_from_urn(code_urn)

        if codelist_id:
            mapping[hierarchy_id] = codelist_id

    return mapping