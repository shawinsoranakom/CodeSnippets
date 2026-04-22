def test_tab_required(self):
        """Test that at least one tab is required."""
        with self.assertRaises(TypeError):
            st.tabs()

        with self.assertRaises(StreamlitAPIException):
            st.tabs([])