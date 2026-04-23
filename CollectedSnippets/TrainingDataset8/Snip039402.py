def test_read_persisted_data(self, mock_read):
        """We should read persisted data from disk on cache miss."""

        @st.experimental_memo(persist="disk")
        def foo():
            return "actual_value"

        data = foo()
        mock_read.assert_called_once()
        self.assertEqual("mock_pickled_value", data)