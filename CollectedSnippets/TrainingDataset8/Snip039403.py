def test_read_bad_persisted_data(self, mock_read):
        """If our persisted data is bad, we raise an exception."""

        @st.experimental_memo(persist="disk")
        def foo():
            return "actual_value"

        with self.assertRaises(CacheError) as error:
            foo()
        mock_read.assert_called_once()
        self.assertEqual("Unable to read from cache", str(error.exception))