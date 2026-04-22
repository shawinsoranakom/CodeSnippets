def test_range_session_state(self):
        """Test a range set by session state."""
        date_range_input = [datetime.today(), datetime.today() + timedelta(2)]
        state = st.session_state
        state["date_range"] = date_range_input[:]

        date_range = st.date_input(
            "select a date range",
            key="date_range",
        )

        assert date_range == date_range_input