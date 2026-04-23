def test_config_blacklist(self, fob):
        """Test server.folderWatchBlacklist"""
        prev_blacklist = config.get_option("server.folderWatchBlacklist")

        config.set_option(
            "server.folderWatchBlacklist", [os.path.dirname(DUMMY_MODULE_1.__file__)]
        )

        lso = local_sources_watcher.LocalSourcesWatcher(SCRIPT_PATH)
        lso.register_file_change_callback(NOOP_CALLBACK)

        fob.assert_called_once()

        sys.modules["DUMMY_MODULE_1"] = DUMMY_MODULE_1
        fob.reset_mock()

        lso.update_watched_modules()

        fob.assert_not_called()

        # Reset the config object.
        config.set_option("server.folderWatchBlacklist", prev_blacklist)