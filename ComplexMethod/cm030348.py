def _handle_preload(preload, main_path=None, sys_path=None, sys_argv=None,
                    on_error='ignore'):
    """Handle module preloading with configurable error handling.

    Args:
        preload: List of module names to preload.
        main_path: Path to __main__ module if '__main__' is in preload.
        sys_path: sys.path to use for imports (None means use current).
        sys_argv: sys.argv to use (None means use current).
        on_error: How to handle import errors ("ignore", "warn", or "fail").
    """
    if not preload:
        return

    if sys_argv is not None:
        sys.argv[:] = sys_argv
    if sys_path is not None:
        sys.path[:] = sys_path

    if '__main__' in preload and main_path is not None:
        process.current_process()._inheriting = True
        try:
            spawn.import_main_path(main_path)
        except Exception as e:
            # Catch broad Exception because import_main_path() uses
            # runpy.run_path() which executes the script and can raise
            # any exception, not just ImportError
            _handle_import_error(
                on_error, f"__main__ from {main_path!r}", e, warn_stacklevel=2
            )
        finally:
            del process.current_process()._inheriting

    for modname in preload:
        try:
            __import__(modname)
        except ImportError as e:
            _handle_import_error(
                on_error, f"module {modname!r}", e, warn_stacklevel=2
            )

    # gh-135335: flush stdout/stderr in case any of the preloaded modules
    # wrote to them, otherwise children might inherit buffered data
    util._flush_std_streams()