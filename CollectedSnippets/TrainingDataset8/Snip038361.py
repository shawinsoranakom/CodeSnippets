def _fix_sys_path(main_script_path: str) -> None:
    """Add the script's folder to the sys path.

    Python normally does this automatically, but since we exec the script
    ourselves we need to do it instead.
    """
    sys.path.insert(0, os.path.dirname(main_script_path))