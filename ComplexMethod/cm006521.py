async def delete_file(
    file_id: uuid.UUID,
    current_user: CurrentActiveUser,
    session: DbSession,
    storage_service: Annotated[StorageService, Depends(get_storage_service)],
):
    """Delete a file by its ID."""
    try:
        # Fetch the file object
        file_to_delete = await fetch_file_object(file_id, current_user, session)
        if not file_to_delete:
            raise HTTPException(status_code=404, detail="File not found")

        # Extract just the filename from the path (strip user_id prefix)
        file_name = Path(file_to_delete.path).name

        # Delete the file from the storage service first
        storage_deleted = False
        try:
            await storage_service.delete_file(flow_id=str(current_user.id), file_name=file_name)
            storage_deleted = True
        except Exception as err:
            # Check if this is a "permanent" failure where file/storage is gone
            # These are safe to delete from DB even if storage deletion failed
            if is_permanent_storage_failure(err):
                await logger.awarning(
                    "File %s not found in storage (permanent failure), will remove from database: %s",
                    file_name,
                    err,
                )
                storage_deleted = True
            else:
                # Transient failure (network, timeout, permissions) - keep in DB for retry
                await logger.awarning(
                    "Failed to delete file %s from storage (transient error, keeping in database for retry): %s",
                    file_name,
                    err,
                )
                # Don't delete from DB - user can retry
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to delete file from storage. Please try again. Error: {err}",
                ) from err

        # Only delete from database if storage deletion succeeded OR it was a permanent failure
        if storage_deleted:
            try:
                await session.delete(file_to_delete)
            except Exception as db_error:
                await logger.aerror(
                    "Failed to delete file %s from database: %s",
                    file_to_delete.name,
                    db_error,
                )
                raise HTTPException(
                    status_code=500, detail=f"Error deleting file from database: {db_error}"
                ) from db_error

            return {"detail": f"File {file_to_delete.name} deleted successfully"}
    except HTTPException:
        # Re-raise HTTPException to avoid being caught by the generic exception handler
        raise
    except Exception as e:
        # Log and return a generic server error
        await logger.aerror("Error deleting file %s: %s", file_id, e)
        raise HTTPException(status_code=500, detail=f"Error deleting file: {e}") from e