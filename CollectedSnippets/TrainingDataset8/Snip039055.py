def test_range_out_of_order(self):
        """Test a range that is out of order."""
        st.select_slider(
            "the label", value=("yellow", "red"), options=["red", "orange", "yellow"]
        )

        c = self.get_delta_from_queue().new_element.slider
        self.assertEqual(c.default, [0, 2])