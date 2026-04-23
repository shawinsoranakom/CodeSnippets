async def download_profile_picture(
    folder_name: ValidatedFolderName,
    file_name: ValidatedFileName,
    settings_service: Annotated[SettingsService, Depends(get_settings_service)],
):
    """Download profile picture from local filesystem.

    Profile pictures are first looked up in config_dir/profile_pictures/,
    then fallback to the package's bundled profile_pictures directory.
    """
    try:
        # Only allow specific folder names (dynamic from config + package)
        allowed_folders = _get_allowed_profile_picture_folders(settings_service)
        if folder_name not in allowed_folders:
            raise HTTPException(status_code=400, detail=f"Folder must be one of: {', '.join(sorted(allowed_folders))}")

        # SECURITY: Extract only the final path component to prevent path traversal.
        # This is defense-in-depth on top of ValidatedFileName/ValidatedFolderName.
        safe_folder = Path(folder_name).name
        safe_file = Path(file_name).name

        extension = safe_file.split(".")[-1]
        config_dir = settings_service.settings.config_dir
        config_path = Path(config_dir).resolve()  # type: ignore[arg-type]

        # Construct the file path
        file_path = (config_path / "profile_pictures" / safe_folder / safe_file).resolve()

        # SECURITY: Verify the resolved path is still within the allowed directory
        # This prevents path traversal even if symbolic links are involved.
        # Uses os.path.normpath + startswith (the pattern recognised by CodeQL as a sanitiser).
        allowed_base = str((config_path / "profile_pictures").resolve())
        if not (str(file_path).startswith(allowed_base + os.sep) or str(file_path) == allowed_base):
            raise HTTPException(status_code=404, detail="Profile picture not found")

        # Fallback to package bundled profile pictures if not found in config_dir
        if not file_path.exists():
            from langflow.initial_setup import setup

            package_base = Path(setup.__file__).parent / "profile_pictures"
            package_path = (package_base / safe_folder / safe_file).resolve()

            # SECURITY: Verify package path is also within allowed directory
            allowed_package_base = str(package_base.resolve())
            pkg_path_str = str(package_path)
            if not (pkg_path_str.startswith(allowed_package_base + os.sep) or pkg_path_str == allowed_package_base):
                raise HTTPException(status_code=404, detail="Profile picture not found")

            if package_path.exists():
                file_path = package_path
            else:
                raise HTTPException(status_code=404, detail=f"Profile picture {safe_folder}/{safe_file} not found")

        content_type = build_content_type_from_extension(extension)
        # Read file directly from local filesystem using async file operations
        file_content = await anyio.Path(file_path).read_bytes()
        return StreamingResponse(BytesIO(file_content), media_type=content_type)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e