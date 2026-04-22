def test_should_show_new_version_notice_skip(self):
        with mock.patch(
            "streamlit.version._get_latest_streamlit_version"
        ) as get_latest:
            version.CHECK_PYPI_PROBABILITY = 0
            self.assertFalse(should_show_new_version_notice())
            get_latest.assert_not_called()