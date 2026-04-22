def test_permission_error(self, fob):
        fob.side_effect = PermissionError("This error should be caught!")
        lso = local_sources_watcher.LocalSourcesWatcher(SCRIPT_PATH)
        lso.register_file_change_callback(NOOP_CALLBACK)