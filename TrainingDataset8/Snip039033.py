def test_horizontal(self):
        """Test that it can be called with horizontal param."""
        st.radio("the label", ("m", "f"), horizontal=True)

        c = self.get_delta_from_queue().new_element.radio
        self.assertEqual(c.horizontal, True)