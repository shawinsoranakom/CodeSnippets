def test_error_on_invalid_formats(self):
        BAD_FORMATS = [
            "blah",
            "a%f",
            "a%.3f",
            "%d%d",
        ]
        for fmt in BAD_FORMATS:
            with pytest.raises(StreamlitAPIException) as exc_message:
                st.number_input("any label", value=3.14, format=fmt)