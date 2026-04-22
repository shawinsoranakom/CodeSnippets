def test_st_info(self):
        """Test st.info."""
        st.info("some info")

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.alert.body, "some info")
        self.assertEqual(el.alert.format, Alert.INFO)