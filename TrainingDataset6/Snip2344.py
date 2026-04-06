def include_path_in_search(path):
    return not any(path.startswith(x) for x in settings.excluded_search_path_prefixes)