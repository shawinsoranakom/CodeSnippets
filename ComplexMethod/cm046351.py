def get_user_config_dir(sub_dir="Ultralytics"):
    """Return a writable config dir, preferring YOLO_CONFIG_DIR and being OS-aware.

    Args:
        sub_dir (str): The name of the subdirectory to create.

    Returns:
        (Path): The path to the user config directory.
    """
    if env_dir := os.getenv("YOLO_CONFIG_DIR"):
        p = Path(env_dir).expanduser() / sub_dir
    elif LINUX:
        p = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / sub_dir
    elif WINDOWS:
        p = Path.home() / "AppData" / "Roaming" / sub_dir
    elif MACOS:
        p = Path.home() / "Library" / "Application Support" / sub_dir
    else:
        raise ValueError(f"Unsupported operating system: {platform.system()}")

    if p.exists():  # already created → trust it
        return p
    if is_dir_writeable(p.parent):  # create if possible
        p.mkdir(parents=True, exist_ok=True)
        return p

    # Fallbacks for Docker, GCP/AWS functions where only /tmp is writable
    for alt in [Path("/tmp") / sub_dir, Path.cwd() / sub_dir]:
        if alt.exists():
            return alt
        if is_dir_writeable(alt.parent):
            alt.mkdir(parents=True, exist_ok=True)
            LOGGER.warning(
                f"user config directory '{p}' is not writable, using '{alt}'. Set YOLO_CONFIG_DIR to override."
            )
            return alt

    # Last fallback → CWD
    p = Path.cwd() / sub_dir
    p.mkdir(parents=True, exist_ok=True)
    return p