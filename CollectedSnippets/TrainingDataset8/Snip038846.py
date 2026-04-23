def test_unwrapped_deltagenerator_func(self):
        """Test unwrapped Streamlit DeltaGenerator function."""
        st.help(st.dataframe)

        ds = self.get_delta_from_queue().new_element.doc_string
        self.assertEqual("dataframe", ds.name)
        self.assertEqual("streamlit", ds.module)
        self.assertEqual("<class 'method'>", ds.type)
        if sys.version_info < (3, 9):
            # Python < 3.9 represents the signature slightly differently
            self.assertEqual(
                "(data: 'Data' = None, width: Union[int, NoneType] = None, "
                "height: Union[int, NoneType] = None, *, use_container_width: bool = False) -> 'DeltaGenerator'",
                ds.signature,
            )
        else:

            self.assertEqual(
                "(data: 'Data' = None, width: Optional[int] = None, "
                "height: Optional[int] = None, *, use_container_width: bool = False) -> 'DeltaGenerator'",
                ds.signature,
            )

        self.assertTrue(ds.doc_string.startswith("Display a dataframe"))