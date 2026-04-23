async def create():
    req = await get_request_json()
    kb_id = req["kb_id"]
    if not kb_id:
        return get_json_result(data=False, message='Lack of "KB ID"', code=RetCode.ARGUMENT_ERROR)
    if len(req["name"].encode("utf-8")) > FILE_NAME_LEN_LIMIT:
        return get_json_result(data=False, message=f"File name must be {FILE_NAME_LEN_LIMIT} bytes or less.", code=RetCode.ARGUMENT_ERROR)

    if req["name"].strip() == "":
        return get_json_result(data=False, message="File name can't be empty.", code=RetCode.ARGUMENT_ERROR)
    req["name"] = req["name"].strip()

    try:
        e, kb = KnowledgebaseService.get_by_id(kb_id)
        if not e:
            return get_data_error_result(message="Can't find this dataset!")

        if DocumentService.query(name=req["name"], kb_id=kb_id):
            return get_data_error_result(message="Duplicated document name in the same dataset.")

        kb_root_folder = FileService.get_kb_folder(kb.tenant_id)
        if not kb_root_folder:
            return get_data_error_result(message="Cannot find the root folder.")
        kb_folder = FileService.new_a_file_from_kb(
            kb.tenant_id,
            kb.name,
            kb_root_folder["id"],
        )
        if not kb_folder:
            return get_data_error_result(message="Cannot find the kb folder for this file.")

        doc = DocumentService.insert(
            {
                "id": get_uuid(),
                "kb_id": kb.id,
                "parser_id": kb.parser_id,
                "pipeline_id": kb.pipeline_id,
                "parser_config": kb.parser_config,
                "created_by": current_user.id,
                "type": FileType.VIRTUAL,
                "name": req["name"],
                "suffix": Path(req["name"]).suffix.lstrip("."),
                "location": "",
                "size": 0,
            }
        )

        FileService.add_file_from_kb(doc.to_dict(), kb_folder["id"], kb.tenant_id)

        return get_json_result(data=doc.to_json())
    except Exception as e:
        return server_error_response(e)