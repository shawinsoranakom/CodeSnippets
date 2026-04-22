def test_bad_columns_list_negative_value(self):
        with self.assertRaises(StreamlitAPIException):
            st.columns([5, 6, -1.2])