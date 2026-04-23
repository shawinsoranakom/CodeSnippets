async def web_crawl():
    form = await request.form
    kb_id = form.get("kb_id")
    if not kb_id:
        return get_json_result(data=False, message='Lack of "KB ID"', code=RetCode.ARGUMENT_ERROR)
    name = form.get("name")
    url = form.get("url")
    if not is_valid_url(url):
        return get_json_result(data=False, message="The URL format is invalid", code=RetCode.ARGUMENT_ERROR)
    e, kb = KnowledgebaseService.get_by_id(kb_id)
    if not e:
        raise LookupError("Can't find this dataset!")
    if not check_kb_team_permission(kb, current_user.id):
        return get_json_result(data=False, message="No authorization.", code=RetCode.AUTHENTICATION_ERROR)

    blob = html2pdf(url)
    if not blob:
        return server_error_response(ValueError("Download failure."))

    root_folder = FileService.get_root_folder(current_user.id)
    pf_id = root_folder["id"]
    FileService.init_knowledgebase_docs(pf_id, current_user.id)
    kb_root_folder = FileService.get_kb_folder(current_user.id)
    kb_folder = FileService.new_a_file_from_kb(kb.tenant_id, kb.name, kb_root_folder["id"])

    try:
        filename = duplicate_name(DocumentService.query, name=name + ".pdf", kb_id=kb.id)
        filetype = filename_type(filename)
        if filetype == FileType.OTHER.value:
            raise RuntimeError("This type of file has not been supported yet!")

        location = filename
        while settings.STORAGE_IMPL.obj_exist(kb_id, location):
            location += "_"
        settings.STORAGE_IMPL.put(kb_id, location, blob)
        doc = {
            "id": get_uuid(),
            "kb_id": kb.id,
            "parser_id": kb.parser_id,
            "parser_config": kb.parser_config,
            "created_by": current_user.id,
            "type": filetype,
            "name": filename,
            "location": location,
            "size": len(blob),
            "thumbnail": thumbnail(filename, blob),
            "suffix": Path(filename).suffix.lstrip("."),
        }
        if doc["type"] == FileType.VISUAL:
            doc["parser_id"] = ParserType.PICTURE.value
        if doc["type"] == FileType.AURAL:
            doc["parser_id"] = ParserType.AUDIO.value
        if re.search(r"\.(ppt|pptx|pages)$", filename):
            doc["parser_id"] = ParserType.PRESENTATION.value
        if re.search(r"\.(eml)$", filename):
            doc["parser_id"] = ParserType.EMAIL.value
        DocumentService.insert(doc)
        FileService.add_file_from_kb(doc, kb_folder["id"], kb.tenant_id)
    except Exception as e:
        return server_error_response(e)
    return get_json_result(data=True)