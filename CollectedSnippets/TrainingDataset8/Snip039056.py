def test_range_session_state(self):
        """Test a range set by session state."""
        state = st.session_state
        state["colors"] = ("red", "orange")

        colors = st.select_slider(
            "select colors",
            options=["red", "orange", "yellow"],
            key="colors",
        )

        assert colors == ("red", "orange")