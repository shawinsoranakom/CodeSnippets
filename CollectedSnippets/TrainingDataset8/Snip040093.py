def test_st_info_with_icon(self):
        """Test st.info with icon."""
        st.info("some info", icon="👉🏻")

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.alert.body, "some info")
        self.assertEqual(el.alert.icon, "👉🏻")
        self.assertEqual(el.alert.format, Alert.INFO)