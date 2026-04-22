def test_set_page_config_layout_invalid(self):
        with self.assertRaises(StreamlitAPIException):
            st.set_page_config(layout="invalid")