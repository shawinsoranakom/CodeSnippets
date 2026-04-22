def test_dict_and_string(self, mock_json, mock_markdown):
        """Test st.write with dict."""
        manager = Mock()
        manager.attach_mock(mock_json, "json")
        manager.attach_mock(mock_markdown, "markdown")

        st.write("here is a dict", {"a": 1, "b": 2}, " and that is all")

        expected_calls = [
            call.markdown("here is a dict", unsafe_allow_html=False),
            call.json({"a": 1, "b": 2}),
            call.markdown(" and that is all", unsafe_allow_html=False),
        ]
        self.assertEqual(manager.mock_calls, expected_calls)