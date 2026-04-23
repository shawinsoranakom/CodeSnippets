async def create_or_upload(tenant_id: str = None):
    """
    Upload files or create a folder.
    ---
    tags:
      - Files
    security:
      - ApiKeyAuth: []
    parameters:
      - in: header
        name: Authorization
        type: string
        required: true
        description: Bearer token for authentication.
    responses:
      200:
        description: Successful operation.
    """
    content_type = request.content_type or ""
    try:
        if "multipart/form-data" in content_type:
            form = await request.form
            pf_id = form.get("parent_id")
            files = await request.files
            if 'file' not in files:
                return get_error_argument_result("No file part!")
            file_objs = files.getlist('file')
            for file_obj in file_objs:
                if file_obj.filename == '':
                    return get_error_argument_result("No file selected!")

            success, result = await file_api_service.upload_file(tenant_id, pf_id, file_objs)
            if success:
                return get_result(data=result)
            else:
                return get_error_data_result(message=result)
        else:
            req, err = await validate_and_parse_json_request(request, CreateFolderReq)
            if err is not None:
                return get_error_argument_result(err)

            success, result = await file_api_service.create_folder(
                tenant_id, req["name"], req.get("parent_id"), req.get("type")
            )
            if success:
                return get_result(data=result)
            else:
                return get_error_data_result(message=result)
    except Exception as e:
        logging.exception(e)
        return get_error_data_result(message="Internal server error")