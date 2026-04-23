async def get_files(
    file_paths: list[str],
    *,
    convert_to_base64: bool = False,
):
    """Get files from storage service."""
    if not file_paths:
        return []

    storage_service = get_storage_service()
    if not storage_service:
        # For testing purposes, read files directly when no storage service
        file_objects: list[str | bytes] = []
        for file_path_str in file_paths:
            if not file_path_str:  # Skip empty paths
                continue

            file_path = Path(file_path_str)
            if file_path.exists():
                # Use async read for compatibility
                try:
                    async with aiofiles.open(file_path, "rb") as f:
                        file_content = await f.read()
                    if convert_to_base64:
                        file_base64 = base64.b64encode(file_content).decode("utf-8")
                        file_objects.append(file_base64)
                    else:
                        file_objects.append(file_content)
                except Exception as e:
                    msg = f"Error reading file {file_path}: {e}"
                    raise FileNotFoundError(msg) from e
            else:
                msg = f"File not found: {file_path}"
                raise FileNotFoundError(msg)
        return file_objects

    file_objects: list[str | bytes] = []
    for file in file_paths:
        if not file:  # Skip empty file paths
            continue

        flow_id, file_name = storage_service.parse_file_path(file)

        if not file_name:  # Skip if no filename
            continue

        if not storage_service:
            continue

        try:
            file_object = await storage_service.get_file(flow_id=flow_id, file_name=file_name)
            if convert_to_base64:
                file_base64 = base64.b64encode(file_object).decode("utf-8")
                file_objects.append(file_base64)
            else:
                file_objects.append(file_object)
        except Exception as e:
            msg = f"Error getting file {file} from storage: {e}"
            raise FileNotFoundError(msg) from e
    return file_objects