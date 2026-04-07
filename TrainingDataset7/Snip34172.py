def test_watch_for_template_changes(self):
        mock_reloader = mock.MagicMock()
        autoreload.watch_for_template_changes(mock_reloader)
        self.assertSequenceEqual(
            sorted(mock_reloader.watch_dir.call_args_list),
            [
                mock.call(ROOT / "templates", "**/*"),
            ],
        )