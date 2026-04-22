def test_empty(self):
        """Test Empty."""
        st.empty()

        element = self.get_delta_from_queue().new_element
        self.assertEqual(element.empty, EmptyProto())