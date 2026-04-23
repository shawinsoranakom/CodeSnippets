async def upload_info():
    files = await request.files
    file_objs = files.getlist("file") if files and files.get("file") else []
    url = request.args.get("url")

    if file_objs and url:
        return get_json_result(
            data=False,
            message="Provide either multipart file(s) or ?url=..., not both.",
            code=RetCode.BAD_REQUEST,
        )

    if not file_objs and not url:
        return get_json_result(
            data=False,
            message="Missing input: provide multipart file(s) or url",
            code=RetCode.BAD_REQUEST,
        )

    try:
        if url and not file_objs:
            return get_json_result(data=FileService.upload_info(current_user.id, None, url))

        if len(file_objs) == 1:
            return get_json_result(data=FileService.upload_info(current_user.id, file_objs[0], None))

        results = [FileService.upload_info(current_user.id, f, None) for f in file_objs]
        return get_json_result(data=results)
    except Exception as e:
        return server_error_response(e)