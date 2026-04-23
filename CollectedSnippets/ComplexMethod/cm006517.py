async def upload_user_file(
    file: Annotated[UploadFile, File(...)],
    session: DbSession,
    current_user: CurrentActiveUser,
    storage_service: Annotated[StorageService, Depends(get_storage_service)],
    settings_service: Annotated[SettingsService, Depends(get_settings_service)],
    *,
    append: bool = False,
    ephemeral: bool = False,
) -> UploadFileResponse:
    """Upload a file for the current user and track it in the database."""
    # Get the max allowed file size from settings (in MB)
    try:
        max_file_size_upload = settings_service.settings.max_file_size_upload
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Settings error: {e}") from e

    # Validate that a file is actually provided
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Validate file size (convert MB to bytes)
    if file.size > max_file_size_upload * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File size is larger than the maximum file size {max_file_size_upload}MB.",
        )

    # Create a new database record for the uploaded file.
    try:
        # SECURITY FIX: Validate and sanitize multipart upload filename to prevent path traversal attacks
        # First, validate the original filename to reject obvious malicious attempts
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        # Reject filenames containing directory traversal sequences or path separators
        # This prevents attackers from using directory traversal in the Content-Disposition header
        # Check for: path separators (/, \), traversal (..), null bytes, and other dangerous chars
        dangerous_chars = ["..", "/", "\\", "\x00", "\n", "\r"]
        if any(char in file.filename for char in dangerous_chars):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid file name. Filename must not contain directory paths, "
                    "'..' sequences, or control characters."
                ),
            )

        # Additional check: reject filenames that are too long (prevent DoS)
        # Most filesystems have a 255 byte limit for filenames
        MAX_FILENAME_BYTES = 255  # noqa: N806
        if len(file.filename.encode("utf-8")) > MAX_FILENAME_BYTES:
            raise HTTPException(
                status_code=400,
                detail="File name is too long. Maximum 255 bytes allowed.",
            )

        # Extract only the basename as an additional safety measure
        # This provides defense-in-depth in case the above checks are bypassed
        new_filename = Path(file.filename).name

        # Final validation: ensure the sanitized filename is valid and not empty
        if not new_filename or new_filename in (".", ".."):
            raise HTTPException(status_code=400, detail="Invalid file name after sanitization")

        # Reject reserved filenames on Windows (CON, PRN, AUX, NUL, COM1-9, LPT1-9)
        # This prevents issues when code runs on Windows systems
        reserved_names = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        }
        name_without_ext = new_filename.rsplit(".", 1)[0].upper()
        if name_without_ext in reserved_names:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file name. '{name_without_ext}' is a reserved system name.",
            )

        # Enforce unique constraint on name, except for the special _mcp_servers file
        try:
            root_filename, file_extension = new_filename.rsplit(".", 1)
        except ValueError:
            root_filename, file_extension = new_filename, ""

        # Special handling for the MCP servers config file: always keep the same root filename
        mcp_file = await get_mcp_file(current_user)
        mcp_file_ext = await get_mcp_file(current_user, extension=True)

        # Initialize existing_file for append mode
        existing_file = None

        if new_filename == mcp_file_ext:
            # Check if an existing record exists; if so, delete it to replace with the new one
            existing_mcp_file = await get_file_by_name(mcp_file, current_user, session)
            if existing_mcp_file:
                await delete_file(existing_mcp_file.id, current_user, session, storage_service)
                # Flush the session to ensure the deletion is committed before creating the new file
                await session.flush()
            unique_filename = new_filename
        elif append:
            # In append mode, check if file exists and reuse the same filename
            existing_file = await get_file_by_name(root_filename, current_user, session)
            if existing_file:
                # File exists, append to it by reusing the same filename
                # Extract the filename from the path
                unique_filename = Path(existing_file.path).name
            else:
                # File doesn't exist yet, create new one with extension
                unique_filename = f"{root_filename}.{file_extension}" if file_extension else root_filename
        else:
            # For normal files, ensure unique name by appending a count if necessary
            stmt = select(UserFile).where(
                col(UserFile.name).like(f"{root_filename}%"), UserFile.user_id == current_user.id
            )
            existing_files = await session.exec(stmt)
            files = existing_files.all()  # Fetch all matching records

            if files:
                counts = []

                # Extract the count from the filename
                for my_file in files:
                    match = re.search(r"\((\d+)\)(?=\.\w+$|$)", my_file.name)
                    if match:
                        counts.append(int(match.group(1)))

                count = max(counts) if counts else 0
                root_filename = f"{root_filename} ({count + 1})"

            # Create the unique filename with extension for storage
            unique_filename = f"{root_filename}.{file_extension}" if file_extension else root_filename

        # Read file content, save with unique filename, and compute file size in one routine
        try:
            file_id, stored_file_name = await save_file_routine(
                file, storage_service, current_user, file_name=unique_filename, append=append
            )
            file_size = await storage_service.get_file_size(
                flow_id=str(current_user.id),
                file_name=stored_file_name,
            )
        except FileNotFoundError as e:
            # S3 bucket doesn't exist or file not found, or file was uploaded but can't be found
            raise HTTPException(status_code=404, detail=str(e)) from e
        except PermissionError as e:
            # Access denied or invalid credentials - return 500 as this is a server config issue
            raise HTTPException(status_code=500, detail="Error accessing storage") from e
        except Exception as e:
            # General error saving file or getting file size
            raise HTTPException(status_code=500, detail=f"Error accessing file: {e}") from e

        if ephemeral:
            # Ephemeral uploads: file is saved to storage (servable for chat history)
            # but no UserFile record is created (won't appear in "My Files")
            file_path = f"{current_user.id}/{stored_file_name}"
            return UploadFileResponse(id=file_id, name=root_filename, path=file_path, size=file_size)

        if append and existing_file:
            existing_file.size = file_size
            session.add(existing_file)
            await session.commit()
            await session.refresh(existing_file)
            new_file = existing_file
        else:
            # Create a new file record
            new_file = UserFile(
                id=file_id,
                user_id=current_user.id,
                name=root_filename,
                path=f"{current_user.id}/{stored_file_name}",
                size=file_size,
            )

        session.add(new_file)
        try:
            await session.flush()
            await session.refresh(new_file)
        except Exception as db_err:
            # Database insert failed - clean up the uploaded file to avoid orphaned files
            try:
                await storage_service.delete_file(flow_id=str(current_user.id), file_name=stored_file_name)
            except OSError as e:
                #  If delete fails, just log the error
                await logger.aerror(f"Failed to clean up uploaded file {stored_file_name}: {e}")

            raise HTTPException(
                status_code=500, detail=f"Error inserting file metadata into database: {db_err}"
            ) from db_err
    except HTTPException:
        # Re-raise HTTP exceptions (like 409 conflicts) without modification
        raise
    except Exception as e:
        # Optionally, you could also delete the file from disk if the DB insert fails.
        raise HTTPException(status_code=500, detail=f"Database error: {e}") from e

    return UploadFileResponse(id=new_file.id, name=new_file.name, path=new_file.path, size=new_file.size)