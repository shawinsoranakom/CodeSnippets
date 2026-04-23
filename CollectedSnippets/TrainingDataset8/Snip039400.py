def test_dont_persist_by_default(self, mock_write):
        @st.experimental_memo
        def foo():
            return "data"

        foo()
        mock_write.assert_not_called()