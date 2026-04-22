def test_namespace_package_unloaded(self, fob):
        import tests.streamlit.watcher.test_data.namespace_package as pkg

        pkg_path = os.path.abspath(pkg.__path__._path[0])

        lsw = local_sources_watcher.LocalSourcesWatcher(SCRIPT_PATH)
        lsw.register_file_change_callback(NOOP_CALLBACK)

        fob.assert_called_once()

        with patch("sys.modules", {"pkg": pkg}):
            lsw.update_watched_modules()

            # Simulate a change to the child module
            lsw.on_file_changed(pkg_path)

            # Assert that both the parent and child are unloaded, ready for reload
            self.assertNotIn("pkg", sys.modules)

        del sys.modules["tests.streamlit.watcher.test_data.namespace_package"]