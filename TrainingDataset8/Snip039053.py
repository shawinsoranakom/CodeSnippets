def test_none_value(self):
        """Test that it allows None as a valid option"""
        st.select_slider("the label", options=[1, None, 3])
        c = self.get_delta_from_queue().new_element.slider
        self.assertEqual(c.default, [1])