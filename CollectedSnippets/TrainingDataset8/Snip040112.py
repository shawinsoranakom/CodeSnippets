def test_st_warning(self):
        """Test st.warning."""
        st.warning("some warning")

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.alert.body, "some warning")
        self.assertEqual(el.alert.format, Alert.WARNING)