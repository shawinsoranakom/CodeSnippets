def process_deprecation(deprecation, top_level=False):
        collection_name = 'removed_from_collection' if top_level else 'collection_name'
        if not isinstance(deprecation, MutableMapping):
            return
        if (is_module or top_level) and 'removed_in' in deprecation:  # used in module deprecations
            callback(deprecation, 'removed_in', collection_name)
        if 'removed_at_date' in deprecation:
            callback(deprecation, 'removed_at_date', collection_name)
        if not (is_module or top_level) and 'version' in deprecation:  # used in plugin option deprecations
            callback(deprecation, 'version', collection_name)