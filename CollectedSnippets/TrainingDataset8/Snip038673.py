def test_nested_columns(self):
        level1, _ = st.columns(2)
        with self.assertRaises(StreamlitAPIException):
            level2, _ = level1.columns(2)