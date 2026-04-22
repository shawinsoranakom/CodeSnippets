def test_st_echo(self):
        """Test st.echo function (since it's from __init__)."""
        st.help(st.echo)

        ds = self.get_delta_from_queue().new_element.doc_string
        self.assertEqual("echo", ds.name)
        self.assertEqual("streamlit", ds.module)
        self.assertEqual("<class 'function'>", ds.type)
        self.assertEqual("(code_location='above')", ds.signature)
        self.assertTrue(ds.doc_string.startswith("Use in a `with` block"))