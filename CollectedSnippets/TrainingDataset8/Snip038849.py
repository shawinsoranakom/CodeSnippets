def test_builtin_func(self):
        """Test a built-in function."""
        st.help(dir)

        ds = self.get_delta_from_queue().new_element.doc_string
        self.assertEqual("dir", ds.name)
        self.assertEqual("builtins", ds.module)
        self.assertEqual("<class 'builtin_function_or_method'>", ds.type)
        self.assertEqual("", ds.signature)
        self.assertTrue(len(ds.doc_string) > 0)