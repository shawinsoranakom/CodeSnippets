def test_bad_columns_single_float(self):
        with self.assertRaises(TypeError):
            st.columns(6.28)