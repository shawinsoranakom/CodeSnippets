def test_bad_columns_list_int_zero_value(self):
        with self.assertRaises(StreamlitAPIException):
            st.columns([5, 0, 1])