async def upload_file(tenant_id: str, pf_id: str, file_objs: list):
    """
    Upload files to a folder.

    :param tenant_id: tenant ID
    :param pf_id: parent folder ID
    :param file_objs: list of file objects from request
    :return: (success, result_list) or (success, error_message)
    """
    if not pf_id:
        root_folder = FileService.get_root_folder(tenant_id)
        pf_id = root_folder["id"]

    e, pf_folder = FileService.get_by_id(pf_id)
    if not e:
        return False, "Can't find this folder!"

    file_res = []
    for file_obj in file_objs:
        MAX_FILE_NUM_PER_USER = int(os.environ.get('MAX_FILE_NUM_PER_USER', 0))
        if 0 < MAX_FILE_NUM_PER_USER <= await thread_pool_exec(DocumentService.get_doc_count, tenant_id):
            return False, "Exceed the maximum file number of a free user!"

        if not file_obj.filename:
            file_obj_names = [pf_folder.name, file_obj.filename]
        else:
            full_path = '/' + file_obj.filename
            file_obj_names = full_path.split('/')
        file_len = len(file_obj_names)

        file_id_list = await thread_pool_exec(FileService.get_id_list_by_id, pf_id, file_obj_names, 1, [pf_id])
        len_id_list = len(file_id_list)

        if file_len != len_id_list:
            e, file = await thread_pool_exec(FileService.get_by_id, file_id_list[len_id_list - 1])
            if not e:
                return False, "Folder not found!"
            last_folder = await thread_pool_exec(
                FileService.create_folder, file, file_id_list[len_id_list - 1], file_obj_names, len_id_list
            )
        else:
            e, file = await thread_pool_exec(FileService.get_by_id, file_id_list[len_id_list - 2])
            if not e:
                return False, "Folder not found!"
            last_folder = await thread_pool_exec(
                FileService.create_folder, file, file_id_list[len_id_list - 2], file_obj_names, len_id_list
            )

        filetype = filename_type(file_obj_names[file_len - 1])
        location = file_obj_names[file_len - 1]
        while await thread_pool_exec(settings.STORAGE_IMPL.obj_exist, last_folder.id, location):
            location += "_"
        blob = await thread_pool_exec(file_obj.read)
        filename = await thread_pool_exec(
            duplicate_name, FileService.query, name=file_obj_names[file_len - 1], parent_id=last_folder.id
        )
        await thread_pool_exec(settings.STORAGE_IMPL.put, last_folder.id, location, blob)
        file_data = {
            "id": get_uuid(),
            "parent_id": last_folder.id,
            "tenant_id": tenant_id,
            "created_by": tenant_id,
            "type": filetype,
            "name": filename,
            "location": location,
            "size": len(blob),
        }
        inserted = await thread_pool_exec(FileService.insert, file_data)
        file_res.append(inserted.to_json())

    return True, file_res