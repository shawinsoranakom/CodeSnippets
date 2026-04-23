async def download_file(
    file_id: uuid.UUID,
    current_user: CurrentActiveUser,
    session: DbSession,
    storage_service: Annotated[StorageService, Depends(get_storage_service)],
    *,
    return_content: bool = False,
):
    """Download a file by its ID or return its content as a string/bytes.

    Args:
        file_id: UUID of the file.
        current_user: Authenticated user.
        session: Database session.
        storage_service: File storage service.
        return_content: If True, return raw content (str) instead of StreamingResponse.

    Returns:
        StreamingResponse for client downloads or str for internal use.
    """
    try:
        # Fetch the file from the DB
        file = await fetch_file_object(file_id, current_user, session)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        # Get the basename of the file path
        file_name = Path(file.path).name

        # If return_content is True, read the file content and return it
        if return_content:
            # For content return, get the full file
            file_content = await storage_service.get_file(flow_id=str(current_user.id), file_name=file_name)
            if file_content is None:
                raise HTTPException(status_code=404, detail="File not found")
            return await read_file_content(file_content, decode=True)

        # Check file exists before streaming (to catch errors before response headers are sent)
        # This is important because once StreamingResponse starts, we can't change the status code
        try:
            await storage_service.get_file_size(flow_id=str(current_user.id), file_name=file_name)
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=f"File not found: {e}") from e

        # Wrap the async generator in byte_stream_generator to ensure proper iteration
        file_stream = storage_service.get_file_stream(flow_id=str(current_user.id), file_name=file_name)
        byte_stream = byte_stream_generator(file_stream)

        # Create the filename with extension
        file_extension = Path(file.path).suffix
        filename_with_extension = f"{file.name}{file_extension}"

        # Return the file as a streaming response
        return StreamingResponse(
            byte_stream,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename_with_extension}"'},
        )

    except HTTPException:
        raise
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"File not found: {e}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {e}") from e