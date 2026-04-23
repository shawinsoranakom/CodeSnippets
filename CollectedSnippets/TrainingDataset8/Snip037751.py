def _make_widget_key(widgets: List[Tuple[str, Any]], cache_type: CacheType) -> str:
    """
    widget_id + widget_value pair -> hash
    """
    func_hasher = hashlib.new("md5")
    for widget_id_val in widgets:
        update_hash(widget_id_val, func_hasher, cache_type)

    return func_hasher.hexdigest()