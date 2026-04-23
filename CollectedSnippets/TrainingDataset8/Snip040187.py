def test_module_caching(self, _fob):
        lso = local_sources_watcher.LocalSourcesWatcher(SCRIPT_PATH)
        lso.register_file_change_callback(NOOP_CALLBACK)

        register = MagicMock()
        lso._register_necessary_watchers = register

        # Updates modules on first run
        lso.update_watched_modules()
        register.assert_called_once()

        # Skips update when module list hasn't changed
        register.reset_mock()
        lso.update_watched_modules()
        register.assert_not_called()

        # Invalidates cache when a new module is imported
        register.reset_mock()
        sys.modules["DUMMY_MODULE_2"] = DUMMY_MODULE_2
        lso.update_watched_modules()
        register.assert_called_once()

        # Skips update when new module is part of cache
        register.reset_mock()
        lso.update_watched_modules()
        register.assert_not_called()