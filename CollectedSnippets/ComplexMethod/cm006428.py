async def list_profile_pictures(
    settings_service: Annotated[SettingsService, Depends(get_settings_service)],
):
    """List profile pictures from local filesystem.

    Profile pictures are first looked up in config_dir/profile_pictures/,
    then fallback to the package's bundled profile_pictures directory.
    """
    try:
        config_dir = settings_service.settings.config_dir
        config_path = Path(config_dir)  # type: ignore[arg-type]

        # Build list for all allowed folders (dynamic)
        allowed_folders = _get_allowed_profile_picture_folders(settings_service)

        results: list[str] = []
        cfg_base = config_path / "profile_pictures"
        if cfg_base.exists():
            for folder in sorted(allowed_folders):
                p = cfg_base / folder
                if p.exists():
                    results += [f"{folder}/{f.name}" for f in p.iterdir() if f.is_file()]

        # Fallback to package if config_dir produced no results
        if not results:
            from langflow.initial_setup import setup

            package_base = Path(setup.__file__).parent / "profile_pictures"
            for folder in sorted(allowed_folders):
                p = package_base / folder
                if p.exists():
                    results += [f"{folder}/{f.name}" for f in p.iterdir() if f.is_file()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return {"files": results}