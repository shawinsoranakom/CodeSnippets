def test_watches_all_page_scripts(self, fob):
        lsw = local_sources_watcher.LocalSourcesWatcher(SCRIPT_PATH)
        lsw.register_file_change_callback(NOOP_CALLBACK)

        args1, _ = fob.call_args_list[0]
        args2, _ = fob.call_args_list[1]

        assert args1[0] == "streamlit_app.py"
        assert args2[0] == "streamlit_app2.py"