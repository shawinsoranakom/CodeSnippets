def update_metadata_to(metadata, meta):
    if not meta:
        return metadata
    if isinstance(meta, str):
        try:
            meta = json_repair.loads(meta)
        except Exception:
            logging.error("Meta data format error.")
            return metadata
    if not isinstance(meta, dict):
        return metadata

    for k, v in meta.items():
        if isinstance(v, list):
            v = [vv for vv in v if isinstance(vv, str)]
            if not v:
                continue
            v = dedupe_list(v)
        if not isinstance(v, list) and not isinstance(v, str):
            continue
        if k not in metadata:
            metadata[k] = v
            continue
        if isinstance(metadata[k], list):
            if isinstance(v, list):
                metadata[k].extend(v)
            else:
                metadata[k].append(v)
            metadata[k] = dedupe_list(metadata[k])
        else:
            metadata[k] = v

    return metadata