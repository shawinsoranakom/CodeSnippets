def test_st_warning_with_icon(self):
        """Test st.warning with icon."""
        st.warning("some warning", icon="⚠️")

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.alert.body, "some warning")
        self.assertEqual(el.alert.icon, "⚠️")
        self.assertEqual(el.alert.format, Alert.WARNING)