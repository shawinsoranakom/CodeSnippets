def test_st_title_with_anchor(self):
        """Test st.title with anchor."""
        st.title("some title", anchor="some-anchor")

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.heading.body, "some title")
        self.assertEqual(el.heading.tag, "h1")
        self.assertEqual(el.heading.anchor, "some-anchor")