def test_misbehaved_module(self, fob, patched_logger):
        lso = local_sources_watcher.LocalSourcesWatcher(SCRIPT_PATH)
        lso.register_file_change_callback(NOOP_CALLBACK)

        fob.assert_called_once()

        sys.modules["MISBEHAVED_MODULE"] = MISBEHAVED_MODULE.MisbehavedModule
        fob.reset_mock()
        lso.update_watched_modules()

        fob.assert_called_once()  # Just __init__.py

        patched_logger.warning.assert_called_once_with(
            "Examining the path of MisbehavedModule raised: Oh noes!"
        )