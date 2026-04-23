async def move_files(uid: str, src_file_ids: list, dest_file_id: str = None, new_name: str = None):
    """
    Move and/or rename files. Follows Linux mv semantics:
    - new_name only: rename in place (no storage operation)
    - dest_file_id only: move to new folder (keep names)
    - both: move and rename simultaneously

    :param uid: user ID
    :param src_file_ids: list of source file IDs
    :param dest_file_id: destination folder ID (optional)
    :param new_name: new name for the file (optional, single file only)
    :return: (success, result) or (success, error_message)
    """
    files = FileService.get_by_ids(src_file_ids)
    if not files:
        return False, "Source files not found!"

    files_dict = {f.id: f for f in files}

    for file_id in src_file_ids:
        file = files_dict.get(file_id)
        if not file:
            return False, "File or folder not found!"
        if not file.tenant_id:
            return False, "Tenant not found!"
        if not check_file_team_permission(file, uid):
            return False, "No authorization."

    dest_folder = None
    if dest_file_id:
        ok, dest_folder = FileService.get_by_id(dest_file_id)
        if not ok or not dest_folder:
            return False, "Parent folder not found!"

    if new_name:
        file = files_dict[src_file_ids[0]]
        if file.type != FileType.FOLDER.value and \
                pathlib.Path(new_name.lower()).suffix != pathlib.Path(file.name.lower()).suffix:
            return False, "The extension of file can't be changed"
        target_parent_id = dest_folder.id if dest_folder else file.parent_id
        for f in FileService.query(name=new_name, parent_id=target_parent_id):
            if f.name == new_name:
                return False, "Duplicated file name in the same folder."

    def _move_entry_recursive(source_file_entry, dest_folder_entry, override_name=None):
        effective_name = override_name or source_file_entry.name

        if source_file_entry.type == FileType.FOLDER.value:
            existing_folder = FileService.query(name=effective_name, parent_id=dest_folder_entry.id)
            if existing_folder:
                new_folder = existing_folder[0]
            else:
                new_folder = FileService.insert({
                    "id": get_uuid(),
                    "parent_id": dest_folder_entry.id,
                    "tenant_id": source_file_entry.tenant_id,
                    "created_by": source_file_entry.tenant_id,
                    "name": effective_name,
                    "location": "",
                    "size": 0,
                    "type": FileType.FOLDER.value,
                })

            sub_files = FileService.list_all_files_by_parent_id(source_file_entry.id)
            for sub_file in sub_files:
                _move_entry_recursive(sub_file, new_folder)

            FileService.delete_by_id(source_file_entry.id)
            return

        # Non-folder file
        need_storage_move = dest_folder_entry.id != source_file_entry.parent_id
        updates = {}

        if need_storage_move:
            new_location = effective_name
            while settings.STORAGE_IMPL.obj_exist(dest_folder_entry.id, new_location):
                new_location += "_"
            try:
                settings.STORAGE_IMPL.move(
                    source_file_entry.parent_id, source_file_entry.location,
                    dest_folder_entry.id, new_location,
                )
            except Exception as storage_err:
                raise RuntimeError(f"Move file failed at storage layer: {str(storage_err)}")
            updates["parent_id"] = dest_folder_entry.id
            updates["location"] = new_location

        if override_name:
            updates["name"] = override_name

        if updates:
            FileService.update_by_id(source_file_entry.id, updates)

        if override_name:
            informs = File2DocumentService.get_by_file_id(source_file_entry.id)
            if informs:
                if not DocumentService.update_by_id(informs[0].document_id, {"name": override_name}):
                    raise RuntimeError("Database error (Document rename)!")

    def _move_or_rename_sync():
        if dest_folder:
            for file in files:
                _move_entry_recursive(file, dest_folder, override_name=new_name)
        else:
            # Pure rename: no storage operation needed
            file = files[0]
            if not FileService.update_by_id(file.id, {"name": new_name}):
                return False, "Database error (File rename)!"
            informs = File2DocumentService.get_by_file_id(file.id)
            if informs:
                if not DocumentService.update_by_id(informs[0].document_id, {"name": new_name}):
                    return False, "Database error (Document rename)!"
        return True, True

    return await thread_pool_exec(_move_or_rename_sync)