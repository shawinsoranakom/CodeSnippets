def test_st_success_with_icon(self):
        """Test st.success with icon."""
        st.success("some success", icon="✅")

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.alert.body, "some success")
        self.assertEqual(el.alert.icon, "✅")
        self.assertEqual(el.alert.format, Alert.SUCCESS)