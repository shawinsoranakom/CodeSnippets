def test_get_installed_streamlit_version(self):
        self.assertIsInstance(_get_installed_streamlit_version(), PkgVersion)