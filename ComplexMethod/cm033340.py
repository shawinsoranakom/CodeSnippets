async def get_artifact(filename):
    try:
        bucket = SANDBOX_ARTIFACT_BUCKET
        # Validate filename: must be uuid hex + allowed extension, nothing else
        basename = os.path.basename(filename)
        if basename != filename or "/" in filename or "\\" in filename:
            return get_data_error_result(message="Invalid filename.")
        ext = os.path.splitext(basename)[1].lower()
        if ext not in ARTIFACT_CONTENT_TYPES:
            return get_data_error_result(message="Invalid file type.")
        data = await thread_pool_exec(settings.STORAGE_IMPL.get, bucket, basename)
        if not data:
            return get_data_error_result(message="Artifact not found.")
        content_type = ARTIFACT_CONTENT_TYPES.get(ext, "application/octet-stream")
        response = await make_response(data)
        safe_filename = re.sub(r"[^\w.\-]", "_", basename)
        apply_safe_file_response_headers(response, content_type, ext)
        if not response.headers.get("Content-Disposition"):
            response.headers.set("Content-Disposition", f'inline; filename="{safe_filename}"')
        return response
    except Exception as e:
        return server_error_response(e)