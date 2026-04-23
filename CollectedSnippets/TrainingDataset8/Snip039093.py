def test_range_session_state(self):
        """Test a range set by session state."""
        state = st.session_state
        state["slider"] = [10, 20]

        slider = st.slider(
            "select a range",
            min_value=0,
            max_value=100,
            key="slider",
        )

        assert slider == [10, 20]