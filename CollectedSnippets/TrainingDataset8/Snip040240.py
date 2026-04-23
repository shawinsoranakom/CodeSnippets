def test_install_pages_watcher(
        self, patched_watch_dir, patched_invalidate_pages_cache
    ):
        bootstrap._install_pages_watcher("/foo/bar/streamlit_app.py")

        args, _ = patched_watch_dir.call_args_list[0]
        on_pages_changed = args[1]

        patched_watch_dir.assert_called_once_with(
            "/foo/bar/pages",
            on_pages_changed,
            glob_pattern="*.py",
            allow_nonexistent=True,
        )

        on_pages_changed("/foo/bar/pages")
        patched_invalidate_pages_cache.assert_called_once()