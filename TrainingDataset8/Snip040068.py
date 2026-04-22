def test_spinner(self):
        """Test st.spinner."""
        with spinner("some text"):
            # Without the timeout, the spinner is sometimes not available
            time.sleep(0.2)
            el = self.get_delta_from_queue().new_element
            self.assertEqual(el.spinner.text, "some text")