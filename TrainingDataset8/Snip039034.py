def test_horizontal_default_value(self):
        """Test that it can called with horizontal param value False by default."""
        st.radio("the label", ("m", "f"))

        c = self.get_delta_from_queue().new_element.radio
        self.assertEqual(c.horizontal, False)