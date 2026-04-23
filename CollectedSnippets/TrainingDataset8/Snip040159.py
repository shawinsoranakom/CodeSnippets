def test_should_show_new_version_notice_outdated(self):
        with mock.patch(
            "streamlit.version._get_latest_streamlit_version"
        ) as get_latest, mock.patch(
            "streamlit.version._get_installed_streamlit_version"
        ) as get_installed:

            version.CHECK_PYPI_PROBABILITY = 1
            get_installed.side_effect = [PkgVersion("1.0.0")]
            get_latest.side_effect = [PkgVersion("1.2.3")]

            self.assertTrue(should_show_new_version_notice())
            get_installed.assert_called_once()
            get_latest.assert_called_once()