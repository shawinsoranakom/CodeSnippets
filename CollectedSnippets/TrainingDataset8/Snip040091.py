def test_st_help(self):
        """Test st.help."""
        st.help(st.header)

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.doc_string.name, "header")
        self.assertEqual(el.doc_string.module, "streamlit")
        self.assertTrue(
            el.doc_string.doc_string.startswith("Display text in header formatting.")
        )
        self.assertEqual(el.doc_string.type, "<class 'method'>")
        if sys.version_info < (3, 9):
            # Python < 3.9 represents the signature slightly differently
            self.assertEqual(
                el.doc_string.signature,
                "(body: object, anchor: Union[str, NoneType] = None) -> 'DeltaGenerator'",
            )
        else:
            self.assertEqual(
                el.doc_string.signature,
                "(body: object, anchor: Optional[str] = None) -> 'DeltaGenerator'",
            )