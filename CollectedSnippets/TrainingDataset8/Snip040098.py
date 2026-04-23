def test_st_progress(self):
        """Test st.progress."""
        st.progress(51)

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.progress.value, 51)