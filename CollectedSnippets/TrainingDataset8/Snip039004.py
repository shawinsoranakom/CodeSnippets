def test_value_outrange(self):
        with pytest.raises(StreamlitAPIException) as exc_message:
            st.number_input("the label", 11, 0, 10)
        assert (
            "The default `value` of 10 must lie between the `min_value` of "
            "11 and the `max_value` of 0, inclusively." == str(exc_message.value)
        )