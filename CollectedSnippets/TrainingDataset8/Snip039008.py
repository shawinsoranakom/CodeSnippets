def test_error_on_unsupported_formatters(self):
        UNSUPPORTED = "pAn"
        for char in UNSUPPORTED:
            with pytest.raises(StreamlitAPIException) as exc_message:
                st.number_input("any label", value=3.14, format="%" + char)