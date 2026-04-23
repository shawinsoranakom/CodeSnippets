def cached_filename_list_(folder_name: str) -> tuple[list[str], dict[str, float], float] | None:
    strong_cache = cache_helper.get(folder_name)
    if strong_cache is not None:
        return strong_cache

    global filename_list_cache
    global folder_names_and_paths
    folder_name = map_legacy(folder_name)
    if folder_name not in filename_list_cache:
        return None
    out = filename_list_cache[folder_name]

    for x in out[1]:
        time_modified = out[1][x]
        folder = x
        if os.path.getmtime(folder) != time_modified:
            return None

    folders = folder_names_and_paths[folder_name]
    for x in folders[0]:
        if os.path.isdir(x):
            if x not in out[1]:
                return None

    return out