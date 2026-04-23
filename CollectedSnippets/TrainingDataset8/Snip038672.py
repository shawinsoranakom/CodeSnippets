def test_bad_columns_list_float_zero_value(self):
        with self.assertRaises(StreamlitAPIException):
            st.columns([5.0, 0.0, 1.0])