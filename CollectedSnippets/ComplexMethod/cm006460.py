async def delete_knowledge_bases_bulk(request: BulkDeleteRequest, current_user: CurrentActiveUser) -> dict[str, object]:
    """Delete multiple knowledge bases."""
    try:
        deleted_count = 0
        not_found_kbs = []

        for kb_name in request.kb_names:
            try:
                kb_path = _resolve_kb_path(kb_name, current_user)
            except HTTPException as exc:
                if exc.status_code == HTTPStatus.NOT_FOUND:
                    not_found_kbs.append(kb_name)
                    continue
                raise  # Re-raise 403 (traversal) and 500 errors

            try:
                if KBStorageHelper.delete_storage(kb_path, kb_name):
                    deleted_count += 1
            except (OSError, PermissionError) as e:
                await logger.aexception("Error deleting knowledge base '%s': %s", kb_name, e)
                # Continue with other deletions even if one fails

        if not_found_kbs and deleted_count == 0:
            raise HTTPException(
                status_code=404, detail="Knowledge bases not found: {}".format(", ".join(not_found_kbs))
            )

        result = {
            "message": f"Successfully deleted {deleted_count} knowledge base(s)",
            "deleted_count": deleted_count,
        }

        if not_found_kbs:
            result["not_found"] = ", ".join(not_found_kbs)

    except HTTPException:
        raise
    except Exception as e:
        await logger.aerror("Error deleting knowledge bases: %s", e)
        raise HTTPException(status_code=500, detail="Error deleting knowledge bases.") from e
    else:
        return result