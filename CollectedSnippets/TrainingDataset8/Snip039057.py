def test_format_func(self):
        """Test that format_func sends down correct strings of the options."""
        DAYS_OF_WEEK = [
            "Sunday",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
        ]
        st.select_slider(
            "the label",
            value=1,
            options=[0, 1, 2, 3, 4, 5, 6],
            format_func=lambda x: DAYS_OF_WEEK[x],
        )

        c = self.get_delta_from_queue().new_element.slider
        self.assertEqual(c.default, [1])
        self.assertEqual(c.options, DAYS_OF_WEEK)