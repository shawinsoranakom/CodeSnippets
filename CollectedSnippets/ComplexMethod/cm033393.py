def _rm_sync():
        for file_id in file_ids:
            e, file = FileService.get_by_id(file_id)
            if not e or not file:
                return False, "File or Folder not found!"
            if not file.tenant_id:
                return False, "Tenant not found!"
            if not check_file_team_permission(file, uid):
                return False, "No authorization."

            if file.source_type == FileSource.KNOWLEDGEBASE:
                continue

            if file.type == FileType.FOLDER.value:
                _delete_folder_recursive(file, uid)
                continue

            _delete_single_file(file)

        return True, True