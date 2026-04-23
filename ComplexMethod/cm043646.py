def get_preset_choices(user_data_path) -> dict:
    """Get a combined map of default and user screener presets."""
    # pylint: disable=import-outside-toplevel
    import shutil
    from pathlib import Path
    from warnings import warn

    PRESETS_PATH = Path(user_data_path) / "presets" / "finviz"
    PRESETS_PATH_DEFAULT = Path(__file__).parent.resolve() / "presets"
    preset_choices: dict = {}

    if PRESETS_PATH_DEFAULT.exists():
        preset_choices.update(
            {
                filepath.name.replace(".ini", ""): filepath
                for filepath in PRESETS_PATH_DEFAULT.iterdir()
                if filepath.suffix == ".ini"
            }
        )

    try:
        # Create the user presets directory if it doesn't exist.
        if not PRESETS_PATH.exists():
            PRESETS_PATH.mkdir(parents=True, exist_ok=True)

        # Copy any missing default presets to the user presets directory.
        for filepath in PRESETS_PATH_DEFAULT.iterdir():
            if filepath.suffix == ".ini":
                target_path = PRESETS_PATH / filepath.name
                if not target_path.exists():
                    shutil.copy(filepath, target_path)

        # Override any default paths to the user path, if they exist.
        if PRESETS_PATH.exists():
            preset_choices.update(
                {
                    filepath.name.replace(".ini", ""): filepath
                    for filepath in PRESETS_PATH.iterdir()
                    if filepath.suffix == ".ini"
                }
            )
    except Exception as e:
        warn(f"Error loading user presets: {e}")

    preset_choices = {
        k: v for k, v in sorted(preset_choices.items()) if k != "screener_template"
    }

    return preset_choices