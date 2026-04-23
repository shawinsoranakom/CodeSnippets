def test_value_out_of_range(self, value, min_date, max_date):
        with raises(StreamlitAPIException) as exc_message:
            st.date_input(
                "the label", value=value, min_value=min_date, max_value=max_date
            )
        if isinstance(value, (date, datetime)):
            value = [value]
        value = [v.date() if isinstance(v, datetime) else v for v in value]
        assert (
            f"The default `value` of {value} must lie between the `min_value` of {min_date.date()} "
            f"and the `max_value` of {max_date.date()}, inclusively."
            == str(exc_message.value)
        )