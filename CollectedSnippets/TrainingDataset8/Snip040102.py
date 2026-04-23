def test_st_subheader(self):
        """Test st.subheader."""
        st.subheader("some subheader")

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.heading.body, "some subheader")
        self.assertEqual(el.heading.tag, "h3")