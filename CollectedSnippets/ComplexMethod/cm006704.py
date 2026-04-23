def get_file_paths(files: list[str | dict]):
    """Get file paths for a list of files."""
    if not files:
        return []

    storage_service = get_storage_service()
    if not storage_service:
        # Extract paths from dicts if present

        extracted_files = []
        cache_dir = Path(user_cache_dir("langflow"))

        for file in files:
            if not file:  # Skip empty/None files
                continue

            # Handle Image objects, dicts, and strings
            if isinstance(file, dict) and "path" in file:
                file_path = file["path"]
            elif hasattr(file, "path") and file.path:
                file_path = file.path
            else:
                file_path = file

            if not file_path:  # Skip empty paths
                continue

            # If it's a relative path like "flow_id/filename", resolve it to cache dir
            path = Path(file_path)
            if not path.is_absolute() and not path.exists():
                # Check if it exists in the cache directory
                cache_path = cache_dir / file_path
                if cache_path.exists():
                    extracted_files.append(str(cache_path))
                else:
                    # Keep the original path if not found
                    extracted_files.append(file_path)
            else:
                extracted_files.append(file_path)
        return extracted_files

    file_paths = []
    for file in files:
        # Handle dict case
        if storage_service is None:
            continue

        if not file:  # Skip empty/None files
            continue

        if isinstance(file, dict) and "path" in file:
            file_path_str = file["path"]
        elif hasattr(file, "path") and file.path:
            file_path_str = file.path
        else:
            file_path_str = file

        if not file_path_str:  # Skip empty paths
            continue

        flow_id, file_name = storage_service.parse_file_path(file_path_str)

        if not file_name:  # Skip if no filename
            continue

        file_paths.append(storage_service.build_full_path(flow_id=flow_id, file_name=file_name))
    return file_paths