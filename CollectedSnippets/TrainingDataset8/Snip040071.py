def test_streamlit_version(self):
        """Test streamlit.__version__."""
        self.assertEqual(__version__, get_version())