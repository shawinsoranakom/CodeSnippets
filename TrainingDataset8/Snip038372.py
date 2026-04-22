def _install_pages_watcher(main_script_path_str: str) -> None:
    def _on_pages_changed(_path: str) -> None:
        invalidate_pages_cache()

    main_script_path = Path(main_script_path_str)
    pages_dir = main_script_path.parent / "pages"

    watch_dir(
        str(pages_dir),
        _on_pages_changed,
        glob_pattern="*.py",
        allow_nonexistent=True,
    )