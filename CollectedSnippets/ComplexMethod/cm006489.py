def _get_safe_flow_path(fs_path: str, user_id: UUID, storage_service: StorageService) -> Path:
    """Get a safe filesystem path for flow storage, restricted to user's flows directory.

    Allows both absolute and relative paths, but ensures they're within the user's flows directory.
    """
    if not fs_path:
        raise HTTPException(status_code=400, detail="fs_path cannot be empty")

    # Normalize path separators first (before security checks to prevent backslash bypass)
    normalized_path = fs_path.replace("\\", "/")

    # Reject directory traversal and null bytes (check normalized path)
    if ".." in normalized_path:
        raise HTTPException(
            status_code=400,
            detail="Invalid fs_path: directory traversal (..) is not allowed",
        )
    if "\x00" in normalized_path:
        raise HTTPException(
            status_code=400,
            detail="Invalid fs_path: null bytes are not allowed",
        )

    # Build the safe base directory path
    base_dir = storage_service.data_dir / "flows" / str(user_id)
    base_dir_str = str(base_dir)

    # Normalize base directory path (resolve to absolute, handle symlinks)
    # resolve() doesn't require the path to exist, it just resolves symlinks
    try:
        base_dir_stdlib = StdlibPath(base_dir_str).resolve()
        base_dir_resolved = str(base_dir_stdlib)
    except (OSError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid base directory: {e}") from e

    # Determine if path is absolute (Unix or Windows style)
    is_absolute = normalized_path.startswith("/") or (len(normalized_path) > 1 and normalized_path[1] == ":")

    if is_absolute:
        # Absolute path - resolve and validate it's within base directory
        try:
            requested_path = StdlibPath(normalized_path).resolve()
            requested_resolved = str(requested_path)
            # Ensure resolved path stays within base (prevent symlink attacks)
            if not requested_resolved.startswith(base_dir_resolved + "/") and requested_resolved != base_dir_resolved:
                raise HTTPException(
                    status_code=400,
                    detail=f"Absolute path must be within your flows directory: {base_dir_resolved}",
                )
            # Reconstruct the path from the base directory + relative portion
            # so the returned value is derived from the safe base, not user input.
            rel = StdlibPath(requested_resolved).relative_to(base_dir_stdlib)
            return Path(str(base_dir_stdlib / rel))
        except HTTPException:
            raise
        except (OSError, ValueError) as e:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid file save path: {e}. "
                    f"Verify that the path is within your flows directory: {base_dir_resolved}"
                ),
            ) from e
    else:
        # Relative path - validate that it's within the base directory
        relative_part = normalized_path.lstrip("/")
        safe_path_stdlib = base_dir_stdlib / relative_part if relative_part else base_dir_stdlib
        try:
            resolved_path = safe_path_stdlib.resolve()
            resolved_str = str(resolved_path)

            # Ensure resolved path stays within base (prevent symlink attacks)
            if not resolved_str.startswith(base_dir_resolved + "/") and resolved_str != base_dir_resolved:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid path: resolves outside allowed directory",
                )
        except (OSError, ValueError) as e:
            raise HTTPException(status_code=400, detail=f"Invalid path: {e}") from e

        # Return the resolved path to prevent TOCTOU symlink attacks
        return Path(resolved_str)