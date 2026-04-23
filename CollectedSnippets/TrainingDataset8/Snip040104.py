def test_st_success(self):
        """Test st.success."""
        st.success("some success")

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.alert.body, "some success")
        self.assertEqual(el.alert.format, Alert.SUCCESS)