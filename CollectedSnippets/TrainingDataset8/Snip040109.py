def test_st_title(self):
        """Test st.title."""
        st.title("some title")

        el = self.get_delta_from_queue().new_element
        self.assertEqual(el.heading.body, "some title")
        self.assertEqual(el.heading.tag, "h1")