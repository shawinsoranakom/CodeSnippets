async def convert():
    req = await get_request_json()
    kb_ids = req["kb_ids"]
    file_ids = req["file_ids"]

    try:
        files = FileService.get_by_ids(file_ids)
        files_set = {file.id: file for file in files}

        # Validate all files exist before starting any work
        for file_id in file_ids:
            if not files_set.get(file_id):
                return get_data_error_result(message="File not found!")

        # Validate all kb_ids exist before scheduling background work
        for kb_id in kb_ids:
            e, _ = KnowledgebaseService.get_by_id(kb_id)
            if not e:
                return get_data_error_result(message="Can't find this dataset!")

        # Expand folders to their innermost file IDs
        all_file_ids = []
        for file_id in file_ids:
            file = files_set[file_id]
            if file.type == FileType.FOLDER.value:
                all_file_ids.extend(FileService.get_all_innermost_file_ids(file_id, []))
            else:
                all_file_ids.append(file_id)

        user_id = current_user.id
        # Run the blocking DB work in a thread so the event loop is not blocked.
        # For large folders this prevents 504 Gateway Timeout by returning as
        # soon as the background task is scheduled.
        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(None, _convert_files, all_file_ids, kb_ids, user_id)
        future.add_done_callback(
            lambda f: logging.error("_convert_files failed: %s", f.exception()) if f.exception() else None
        )
        return get_json_result(data=True)
    except Exception as e:
        return server_error_response(e)