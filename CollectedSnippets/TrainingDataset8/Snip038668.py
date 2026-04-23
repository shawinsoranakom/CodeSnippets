def test_bad_columns_negative_int(self):
        with self.assertRaises(StreamlitAPIException):
            st.columns(-1337)