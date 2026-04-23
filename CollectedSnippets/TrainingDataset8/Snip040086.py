def test_st_error(self):
        """Test st.error."""
        st.error("some error")

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.alert.body, "some error")
        self.assertEqual(el.alert.format, Alert.ERROR)