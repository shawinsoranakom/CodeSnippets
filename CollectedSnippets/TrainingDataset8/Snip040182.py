def test_nested_module_parent_unloaded(self, fob):
        lso = local_sources_watcher.LocalSourcesWatcher(SCRIPT_PATH)
        lso.register_file_change_callback(NOOP_CALLBACK)

        fob.assert_called_once()

        with patch(
            "sys.modules",
            {
                "DUMMY_MODULE_1": DUMMY_MODULE_1,
                "NESTED_MODULE_PARENT": NESTED_MODULE_PARENT,
                "NESTED_MODULE_CHILD": NESTED_MODULE_CHILD,
            },
        ):
            lso.update_watched_modules()

            # Simulate a change to the child module
            lso.on_file_changed(NESTED_MODULE_CHILD_FILE)

            # Assert that both the parent and child are unloaded, ready for reload
            self.assertNotIn("NESTED_MODULE_CHILD", sys.modules)
            self.assertNotIn("NESTED_MODULE_PARENT", sys.modules)