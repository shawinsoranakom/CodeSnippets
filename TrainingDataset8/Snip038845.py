def test_deltagenerator_func(self):
        """Test Streamlit DeltaGenerator function."""

        st.help(st.audio)

        ds = self.get_delta_from_queue().new_element.doc_string
        self.assertEqual("audio", ds.name)
        self.assertEqual("streamlit", ds.module)
        self.assertEqual("<class 'method'>", ds.type)

        if sys.version_info < (3, 9):
            # Python < 3.9 represents the signature slightly differently
            self.assertEqual(
                "(data: Union[str, bytes, _io.BytesIO, io.RawIOBase, "
                "_io.BufferedReader, ForwardRef('npt.NDArray[Any]'), NoneType], "
                "format: str = 'audio/wav', start_time: int = 0, *, "
                "sample_rate: Union[int, NoneType] = None) -> 'DeltaGenerator'",
                ds.signature,
            )
        else:
            self.assertEqual(
                "(data: Union[str, bytes, _io.BytesIO, io.RawIOBase, "
                "_io.BufferedReader, ForwardRef('npt.NDArray[Any]'), NoneType], "
                "format: str = 'audio/wav', start_time: int = 0, *, "
                "sample_rate: Optional[int] = None) -> 'DeltaGenerator'",
                ds.signature,
            )

        self.assertTrue(ds.doc_string.startswith("Display an audio player"))