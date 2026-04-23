async def delete_files_batch(
    file_ids: list[uuid.UUID],
    current_user: CurrentActiveUser,
    session: DbSession,
    storage_service: Annotated[StorageService, Depends(get_storage_service)],
):
    """Delete multiple files by their IDs."""
    try:
        # Fetch all files from the DB
        stmt = select(UserFile).where(col(UserFile.id).in_(file_ids), col(UserFile.user_id) == current_user.id)
        results = await session.exec(stmt)
        files = results.all()

        if not files:
            raise HTTPException(status_code=404, detail="No files found")

        # Track storage deletion failures
        storage_failures = []
        # Track database deletion failures
        db_failures = []

        # Delete all files from the storage service
        for file in files:
            # Extract just the filename from the path (strip user_id prefix)
            file_name = Path(file.path).name
            storage_deleted = False

            try:
                await storage_service.delete_file(flow_id=str(current_user.id), file_name=file_name)
                storage_deleted = True
            except OSError as err:
                # Check if this is a "permanent" failure where file/storage is gone
                # These are safe to delete from DB even if storage deletion failed
                if is_permanent_storage_failure(err):
                    # File/storage is permanently gone - safe to delete from DB
                    await logger.awarning(
                        "File %s not found in storage (permanent failure), will remove from database: %s",
                        file_name,
                        err,
                    )
                    storage_deleted = True  # Treat as "deleted" for DB purposes
                else:
                    # Transient failure (network, timeout, permissions) - keep in DB for retry
                    storage_failures.append(f"{file_name}: {err}")
                    await logger.awarning(
                        "Failed to delete file %s from storage (transient error, keeping in database for retry): %s",
                        file_name,
                        err,
                    )

            # Only delete from database if storage deletion succeeded OR it was a permanent failure
            if storage_deleted:
                try:
                    await session.delete(file)
                except OSError as db_error:
                    # Log database deletion failure but continue processing remaining files
                    db_failures.append(f"{file_name}: {db_error}")
                    await logger.aerror(
                        "Failed to delete file %s from database: %s",
                        file_name,
                        db_error,
                    )

        # If there were storage failures, include them in the response
        if storage_failures:
            await logger.awarning(
                "Batch delete completed with %d storage failures: %s", len(storage_failures), storage_failures
            )
        # If there were database failures, log them
        if db_failures:
            await logger.aerror("Batch delete completed with %d database failures: %s", len(db_failures), db_failures)
            # If all database deletions failed, raise an error
            if len(db_failures) == len(files):
                raise HTTPException(status_code=500, detail=f"Failed to delete any files from database: {db_failures}")

        # Calculate how many files were actually deleted from database
        # Files successfully deleted = total - (kept due to transient storage failures) - (DB deletion failures)
        files_deleted = len(files) - len(storage_failures) - len(db_failures)
        files_kept = len(storage_failures)  # Files with transient storage failures kept in DB

        # Build response message
        if files_deleted == len(files):
            message = f"{files_deleted} files deleted successfully"
        elif files_deleted > 0:
            message = f"{files_deleted} files deleted successfully"
            if files_kept > 0:
                message += f", {files_kept} files kept in database due to transient storage errors (can retry)"
        else:
            message = "No files were deleted from database"

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting files: {e}") from e

    return {"message": message}