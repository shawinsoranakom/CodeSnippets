def test_equal_columns(self):
        for column in st.columns(4):
            self.assertIsInstance(column, DeltaGenerator)
            self.assertFalse(column._cursor.is_locked)