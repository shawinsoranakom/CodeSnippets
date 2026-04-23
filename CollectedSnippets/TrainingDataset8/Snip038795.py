def test_invalid_string(self):
        """Tests that when the string doesn't match regex, an exception is generated"""
        with pytest.raises(StreamlitAPIException) as exc_message:
            st.color_picker("the label", "#invalid-string")