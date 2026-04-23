def test_does_not_rerun_if_not_current_page(self):
        session = _create_test_session()
        session._run_on_save = True
        session.request_rerun = MagicMock()
        session._on_source_file_changed("/fake/script_path.py")

        self.assertEqual(session.request_rerun.called, False)