def test_builtin_obj(self):
        """Test a built-in function."""
        st.help(123)

        ds = self.get_delta_from_queue().new_element.doc_string
        self.assertEqual("", ds.name)
        self.assertEqual("", ds.module)
        self.assertEqual("<class 'int'>", ds.type)
        self.assertEqual("", ds.signature)
        self.assertTrue(len(ds.doc_string) > 0)