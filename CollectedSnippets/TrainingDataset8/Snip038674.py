def test_nested_expanders(self):
        level1 = st.expander("level 1")
        with self.assertRaises(StreamlitAPIException):
            level1.expander("level 2")