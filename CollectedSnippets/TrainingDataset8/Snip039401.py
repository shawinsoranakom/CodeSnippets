def test_persist_path(self, mock_write):
        """Ensure we're writing to ~/.streamlit/cache/*.memo"""

        @st.experimental_memo(persist="disk")
        def foo():
            return "data"

        foo()
        mock_write.assert_called_once()

        write_path = mock_write.call_args[0][0]
        match = re.fullmatch(
            r"/mock/home/folder/.streamlit/cache/.*?\.memo", write_path
        )
        self.assertIsNotNone(match)