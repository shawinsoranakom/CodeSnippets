def _get_main_script_directory() -> str:
        """Get the absolute path to directory of the main script."""
        import pathlib

        import __main__

        # This works because we set __main__.__file__ to the
        # script path in ScriptRunner.
        abs_main_path = pathlib.Path(__main__.__file__).resolve()
        return str(abs_main_path.parent)