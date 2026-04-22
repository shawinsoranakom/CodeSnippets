def test_progress_int(self):
        """Test Progress with int values."""
        values = [0, 42, 100]
        for value in values:
            st.progress(value)

            element = self.get_delta_from_queue().new_element
            self.assertEqual(value, element.progress.value)