def test_st_header_with_anchor(self):
        """Test st.header with anchor."""
        st.header("some header", anchor="some-anchor")

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.heading.body, "some header")
        self.assertEqual(el.heading.tag, "h2")
        self.assertEqual(el.heading.anchor, "some-anchor")