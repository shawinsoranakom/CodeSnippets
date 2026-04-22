def test_st_subheader_with_anchor(self):
        """Test st.subheader with anchor."""
        st.subheader("some subheader", anchor="some-anchor")

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.heading.body, "some subheader")
        self.assertEqual(el.heading.tag, "h3")
        self.assertEqual(el.heading.anchor, "some-anchor")