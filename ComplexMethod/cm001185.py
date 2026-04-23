async def upload_app_logo(
    app_id: str,
    file: UploadFile,
    user_id: str = Security(get_user_id),
) -> OAuthApplicationInfo:
    """
    Upload a logo image for an OAuth application.

    Requirements:
    - Image must be square (1:1 aspect ratio)
    - Minimum 512x512 pixels
    - Maximum 2048x2048 pixels
    - Allowed formats: JPEG, PNG, WebP
    - Maximum file size: 3MB

    The image is uploaded to cloud storage and the app's logoUrl is updated.
    Returns the updated application info.
    """
    # Verify ownership to reduce vulnerability to DoS(torage) or DoM(oney) attacks
    if (
        not (app := await get_oauth_application_by_id(app_id))
        or app.owner_id != user_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OAuth App not found",
        )

    # Check GCS configuration
    if not settings.config.media_gcs_bucket_name:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Media storage is not configured",
        )

    # Validate content type
    content_type = file.content_type
    if content_type not in LOGO_ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: JPEG, PNG, WebP. Got: {content_type}",
        )

    # Read file content
    try:
        file_bytes = await file.read()
    except Exception as e:
        logger.error(f"Error reading logo file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read uploaded file",
        )

    # Check file size
    if len(file_bytes) > LOGO_MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "File too large. "
                f"Maximum size is {LOGO_MAX_FILE_SIZE // 1024 // 1024}MB"
            ),
        )

    # Validate image dimensions
    try:
        image = Image.open(io.BytesIO(file_bytes))
        width, height = image.size

        if width != height:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Logo must be square. Got {width}x{height}",
            )

        if width < LOGO_MIN_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Logo too small. Minimum {LOGO_MIN_SIZE}x{LOGO_MIN_SIZE}. "
                f"Got {width}x{height}",
            )

        if width > LOGO_MAX_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Logo too large. Maximum {LOGO_MAX_SIZE}x{LOGO_MAX_SIZE}. "
                f"Got {width}x{height}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating logo image: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file",
        )

    # Scan for viruses
    filename = file.filename or "logo"
    await scan_content_safe(file_bytes, filename=filename)

    # Generate unique filename
    file_ext = os.path.splitext(filename)[1].lower() or ".png"
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    storage_path = f"oauth-apps/{app_id}/logo/{unique_filename}"

    # Upload to GCS
    try:
        async with async_storage.Storage() as async_client:
            bucket_name = settings.config.media_gcs_bucket_name

            await async_client.upload(
                bucket_name, storage_path, file_bytes, content_type=content_type
            )

            logo_url = f"https://storage.googleapis.com/{bucket_name}/{storage_path}"
    except Exception as e:
        logger.error(f"Error uploading logo to GCS: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload logo",
        )

    # Delete the current app logo file (if any and it's in our cloud storage)
    await _delete_app_current_logo_file(app)

    # Update the app with the new logo URL
    updated_app = await update_oauth_application(
        app_id=app_id,
        owner_id=user_id,
        logo_url=logo_url,
    )

    if not updated_app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found or you don't have permission to update it",
        )

    logger.info(
        f"OAuth app {updated_app.name} (#{app_id}) logo uploaded by user #{user_id}"
    )

    return updated_app