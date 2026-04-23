def _get_allowed_profile_picture_folders(settings_service: SettingsService) -> set[str]:
    """Return the set of allowed profile picture folders.

    This enumerates subdirectories under the profile_pictures directory in both
    the user's config_dir and the package's bundled assets. This makes the API
    flexible (users may add new folders under config_dir/profile_pictures) while
    still safe because we only ever serve files contained within the resolved
    base directory and validate path containment below.

    If no directories can be found (unexpected), fall back to the curated
    defaults {"People", "Space"} shipped with Langflow.
    """
    allowed: set[str] = set()
    try:
        # Config-provided folders
        config_dir = Path(settings_service.settings.config_dir)
        cfg_base = config_dir / "profile_pictures"
        if cfg_base.exists():
            allowed.update({p.name for p in cfg_base.iterdir() if p.is_dir()})
        # Package-provided folders
        from langflow.initial_setup import setup

        pkg_base = Path(setup.__file__).parent / "profile_pictures"
        if pkg_base.exists():
            allowed.update({p.name for p in pkg_base.iterdir() if p.is_dir()})
    except Exception as _:
        import logging

        logger = logging.getLogger(__name__)
        logger.exception("Exception occurred while getting allowed profile picture folders")

    # Sensible defaults ensure tests and OOTB behavior
    return allowed or {"People", "Space"}