def test_st_error_with_icon(self):
        """Test st.error with icon."""
        st.error("some error", icon="😱")

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.alert.body, "some error")
        self.assertEqual(el.alert.icon, "😱")
        self.assertEqual(el.alert.format, Alert.ERROR)