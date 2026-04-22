def test_st_empty(self):
        """Test st.empty."""
        st.empty()

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.empty, EmptyProto())