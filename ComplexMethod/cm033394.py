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