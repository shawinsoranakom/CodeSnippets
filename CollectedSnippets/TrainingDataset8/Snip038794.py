def test_invalid_value_type_error(self):
        """Tests that when the value type is invalid, an exception is generated"""
        with pytest.raises(StreamlitAPIException) as exc_message:
            st.color_picker("the label", 1234567)