def test_on_pages_changed(self, mock_enqueue: MagicMock):
        session = _create_test_session()
        session._on_pages_changed("/foo/pages")

        expected_msg = ForwardMsg()
        expected_msg.pages_changed.app_pages.extend(
            [
                AppPage(page_script_hash="hash1", page_name="page1", icon=""),
                AppPage(page_script_hash="hash2", page_name="page2", icon="🎉"),
            ]
        )

        mock_enqueue.assert_called_once_with(expected_msg)