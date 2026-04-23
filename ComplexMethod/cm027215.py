def gather_ids(api_data: dict[str, Any]) -> dict[str, Any]:
    """Return dict with IDs."""
    ids: dict[str, Any] = {}

    dev_idx = 1
    for dev_id in api_data[RAW_DEVICES_STATUS]:
        if dev_id not in ids:
            ids[dev_id] = f"device{dev_idx}"
            dev_idx += 1

    group_idx = 1
    inst_idx = 1
    for inst_id, inst_data in api_data[RAW_INSTALLATIONS].items():
        if inst_id not in ids:
            ids[inst_id] = f"installation{inst_idx}"
            inst_idx += 1
        for group in inst_data[API_GROUPS]:
            group_id = group[API_GROUP_ID]
            if group_id not in ids:
                ids[group_id] = f"group{group_idx}"
                group_idx += 1

    ws_idx = 1
    for ws_id in api_data[RAW_WEBSERVERS]:
        if ws_id not in ids:
            ids[ws_id] = f"webserver{ws_idx}"
            ws_idx += 1

    return ids